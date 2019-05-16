from __future__ import absolute_import, print_function

import gzip
import hashlib
import json
import os
import uuid
from collections import defaultdict

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import s3fs
import six
from botocore.exceptions import ClientError
from pyarrow.filesystem import S3FSWrapper  # noqa
from six.moves import queue

from .BaseAggregator import RECORD_TYPE_CONTENT, BaseAggregator, BaseListener
from .parquet_schema import PQ_SCHEMAS

SITE_VISITS_INDEX = '_site_visits_index'
CONTENT_DIRECTORY = 'content'
CONFIG_DIRECTORY = 'config'
VISITS_DIRECTORY = 'visits'
SITE_INDEX_DIR = 'site_index'


def listener_process_runner(
        manager_params, status_queue, shutdown_queue, instance_id):
    """ParquetListener runner. Pass to new process"""
    listener = ParquetListener(
        status_queue, shutdown_queue, manager_params, instance_id)
    listener.startup()

    while True:
        listener.update_status_queue()
        if listener.should_shutdown():
            break
        try:
            record = listener.record_queue.get(block=True, timeout=5)
            listener.process_record(record)
        except queue.Empty:
            pass

    listener.drain_queue()
    listener.shutdown()


class ParquetListener(BaseListener):
    """Listener that saves records to parquet, either locally or on S3.

    Records for each page visit are stored in memory for a batch of sites with
    size given in `manager_params['parquet_batch_size']`. Once the batch size
    is met (or the crawl has finished), the data is written to persistent
    storage.
    The schema for this dataset is given in ./parquet_schema.py
    """
    def __init__(
            self, status_queue, shutdown_queue, manager_params, instance_id):
        if type(manager_params['parquet_batch_size']) != int:
            raise ValueError(
                "ParquetAggregator batch size specified in `manager_params` "
                "must be an integer.")
        self._batch_size = manager_params['parquet_batch_size']
        self.browser_map = dict()  # maps crawl_id to visit_id
        self._records = dict()  # maps visit_id and table to records
        self._batches = dict()  # maps table_name to a list of batches
        self._instance_id = instance_id

        if manager_params['output_format'] == 's3':
            self._output_type = 's3'
            self.dir = manager_params['s3_directory']
            self._bucket = manager_params['s3_bucket']
            self._s3 = boto3.client('s3')
            self._s3_resource = boto3.resource('s3')
            self._fs = s3fs.S3FileSystem()
            self._dataset_root_path = 's3://%s/%s/%s/%%s' % (
                self._bucket, self.dir, VISITS_DIRECTORY)
        elif manager_params['output_format'] == 'local_parquet':
            self._output_type = 'local'
            self.dir = os.path.expanduser(manager_params['data_directory'])
            self._fs = None
            self._dataset_root_path = os.path.join(
                self.dir, VISITS_DIRECTORY, '%s')
        else:
            raise ValueError(
                "The ParquetAggregator supports saving data to the local disk "
                "(`local_parquet`) or to Amazon S3 (`s3`). You set "
                "manager_params['output_format'] to %s." %
                manager_params['output_format']
            )
        super(ParquetListener, self).__init__(
            status_queue, shutdown_queue, manager_params)

    def _get_records(self, visit_id):
        """Get the RecordBatch corresponding to `visit_id`"""
        if visit_id not in self._records:
            self._records[visit_id] = defaultdict(list)
        return self._records[visit_id]

    def _write_record(self, table, data, visit_id):
        """Insert data into a RecordBatch"""
        records = self._get_records(visit_id)
        # Add nulls
        for item in PQ_SCHEMAS[table].names:
            if item not in data:
                data[item] = None
        # Add instance_id (for partitioning)
        data['instance_id'] = self._instance_id
        records[table].append(data)

    def _create_batch(self, visit_id):
        """Create record batches for all records from `visit_id`"""
        for table_name, data in self._records[visit_id].items():
            if table_name not in self._batches:
                self._batches[table_name] = list()
            try:
                df = pd.DataFrame(data)
                batch = pa.RecordBatch.from_pandas(
                    df, schema=PQ_SCHEMAS[table_name], preserve_index=False
                )
                self._batches[table_name].append(batch)
                self.logger.debug(
                    "Successfully created batch for table %s and "
                    "visit_id %s" % (table_name, visit_id)
                )
            except pa.lib.ArrowInvalid as e:
                self.logger.error(
                    "Error while creating record batch:\n%s\n%s\n%s\n"
                    % (table_name, type(e), e)
                )
                pass

            # We construct a special index file from the site_visits data
            # to make it easier to query the dataset
            if table_name == 'site_visits':
                if SITE_VISITS_INDEX not in self._batches:
                    self._batches[SITE_VISITS_INDEX] = list()
                for item in data:
                    self._batches[SITE_VISITS_INDEX].append(item)

        del self._records[visit_id]

    def _exists_on_s3(self, filename):
        """Check if `filename` already exists on S3"""
        try:
            self._s3_resource.Object(self._bucket, filename).load()
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise
        return True

    def _write_str_to_s3(self, string, filename,
                         compressed=True, skip_if_exists=True):
        """Write `string` data to S3 with name `filename`"""
        if skip_if_exists and self._exists_on_s3(filename):
            self.logger.debug(
                "File `%s` already exists on s3, skipping..." % filename)
            return
        if compressed:
            out_f = six.BytesIO()
            with gzip.GzipFile(fileobj=out_f, mode='w') as writer:
                writer.write(string)
            out_f.seek(0)
        else:
            out_f = six.BytesIO(string)

        # Upload to S3
        try:
            self._s3.upload_fileobj(out_f, self._bucket, filename)
            self.logger.debug(
                "Successfully uploaded file `%s` to S3." % filename)
        except Exception as e:
            self.logger.error(
                "Exception while uploading %s\n%s\n%s" % (
                    filename, type(e), e)
            )
            pass

    def _write_str(self, string, filename,
                   compressed=True, skip_if_exists=True):
        """Write `string` data to disk with `filename`"""
        if not isinstance(string, six.binary_type):
            string = string.encode('utf-8')

        # First, check if we should write to S3
        if self._output_type == 's3':
            self._write_str_to_s3(string, filename, compressed, skip_if_exists)
            return

        # Otherwise, write to local disk
        if skip_if_exists and os.path.isfile(filename):
            return
        if not os.path.isdir(os.path.dirname(filename)):
            os.mkdir(os.path.dirname(filename))
        if compressed:
            with gzip.open(filename, 'wb') as f:
                f.write(string)
        else:
            with open(filename, 'w') as f:
                f.write(string)

    def _save_to_dataset(self, force=False):
        """Copy in-memory batches to the parquet dataset"""
        for table_name, batches in self._batches.items():
            if not force and len(batches) <= self._batch_size:
                continue
            if table_name == SITE_VISITS_INDEX:
                out_str = '\n'.join([json.dumps(x) for x in batches])
                if not isinstance(out_str, six.binary_type):
                    out_str = out_str.encode('utf-8')
                fname = '%s/%s/instance-%s-%s.json.gz' % (
                    self.dir, SITE_INDEX_DIR, self._instance_id,
                    hashlib.md5(out_str).hexdigest()
                )
                self._write_str(out_str, fname, compressed=True)
            else:
                try:
                    table = pa.Table.from_batches(batches)
                    pq.write_to_dataset(
                        table, self._dataset_root_path % table_name,
                        filesystem=self._fs,
                        preserve_index=False,
                        partition_cols=['instance_id'],
                        compression='snappy',
                        flavor='spark'
                    )
                except pa.lib.ArrowInvalid as e:
                    self.logger.error(
                        "Error while sending record:\n%s\n%s\n%s\n"
                        % (table_name, type(e), e)
                    )
                    pass
            self._batches[table_name] = list()

    def process_record(self, record):
        """Add `record` to database"""
        if len(record) != 2:
            self.logger.error("Query is not the correct length")
            return

        table, data = record
        if table == "create_table":  # drop these statements
            return
        elif table == RECORD_TYPE_CONTENT:
            self.process_content(record)
            return

        # All data records should be keyed by the crawler and site visit
        try:
            visit_id = data['visit_id']
        except KeyError:
            self.logger.error("Record for table %s has no visit id" % table)
            self.logger.error(json.dumps(data))
            return
        try:
            crawl_id = data['crawl_id']
        except KeyError:
            self.logger.error("Record for table %s has no crawl id" % table)
            self.logger.error(json.dumps(data))
            return

        # Check if the browser for this record has moved on to a new visit
        if crawl_id not in self.browser_map:
            self.browser_map[crawl_id] = visit_id
        elif self.browser_map[crawl_id] != visit_id:
            self._create_batch(self.browser_map[crawl_id])
            self._save_to_dataset()
            self.browser_map[crawl_id] = visit_id

        # Convert data to text type
        for k, v in data.items():
            if isinstance(v, six.binary_type):
                data[k] = six.text_type(v, errors='ignore')
            elif callable(v):
                data[k] = six.text_type(v)
            # TODO: Can we fix this in the extension?
            elif type(v) == dict:
                data[k] = json.dumps(v)
            if k == 'visit_id':
                print(table)
                print('\n\n'+k)
                print(type(v))
                print(v)

        # Save record to disk
        self._write_record(table, data, visit_id)

    def process_content(self, record):
        """Save page content `record` to persistent storage"""
        if record[0] != RECORD_TYPE_CONTENT:
            raise ValueError(
                "Incorrect record type passed to `process_content`. Expected "
                "record of type `%s`, received `%s`." % (
                    RECORD_TYPE_CONTENT, record[0])
            )
        content, content_hash = record[1]
        fname = "%s/%s/%s.gz" % (self.dir, CONTENT_DIRECTORY, content_hash)
        self._write_str(content, fname, compressed=True)

    def drain_queue(self):
        """Process remaining records in queue and save to storage"""
        super(ParquetListener, self).drain_queue()
        self._save_to_dataset(force=True)


class ParquetAggregator(BaseAggregator):
    """
    Receives data records from other processes and aggregates them locally
    per-site before saving to a Parquet dataset. The dataset can be written
    to disk, or saved remotely to S3 and are partitioned by the crawl_id and
    visit_id of each record.

    The visit and task ids are randomly generated to allow multiple writers
    to write to the same S3 bucket. Every record should have a `visit_id`
    (which identifies the site visit) and a `crawl_id` (which identifies the
    browser instance) so we can associate records with the appropriate meta
    data. Any records which lack this information will be dropped by the
    writer.

    Note: Parquet's partitioned dataset reader only supports integer partition
    columns up to 32 bits. Currently, `instance_id` is the only partition
    column, and thus can be no larger than 32 bits.
    """
    def __init__(self, manager_params, browser_params):
        super(ParquetAggregator, self).__init__(manager_params, browser_params)
        self._instance_id = (uuid.uuid4().int & (1 << 32) - 1) - 2**31
        if manager_params['output_format'] == 's3':
            self._output_type = 's3'
            self.dir = manager_params['s3_directory']
            self.bucket = manager_params['s3_bucket']
            self.s3 = boto3.client('s3')
            self._create_bucket()
        elif manager_params['output_format'] == 'local_parquet':
            self._output_type = 'local'
            self.dir = os.path.expanduser(manager_params['data_directory'])
        else:
            raise ValueError(
                "The ParquetAggregator supports saving data to the local disk "
                "(`local`) or to Amazon S3 (`s3`). You set "
                "manager_params['output_format'] to %s." %
                manager_params['output_format']
            )

    def _create_bucket(self):
        """Create remote S3 bucket if it doesn't exist"""
        resource = boto3.resource('s3')
        try:
            resource.meta.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                resource.create_bucket(Bucket=self.bucket)
            else:
                raise

    def save_configuration(self, openwpm_version, browser_version):
        """Save configuration details for this crawl to the database"""

        # Save config keyed by task id
        fname = "%s/%s/instance-%s_configuration.json" % (
            self.dir, CONFIG_DIRECTORY, self._instance_id)

        # Config parameters for update
        out = dict()
        out['manager_params'] = self.manager_params
        out['openwpm_version'] = six.text_type(openwpm_version)
        out['browser_version'] = six.text_type(browser_version)
        out['browser_params'] = self.browser_params
        out_str = json.dumps(out)
        if not isinstance(out_str, six.binary_type):
            out_str = out_str.encode('utf-8')

        # Upload to S3 if enabled
        if self._output_type == 's3':
            out_f = six.BytesIO(out_str)
            try:
                self.s3.upload_fileobj(out_f, self.bucket, fname)
            except Exception:
                self.logger.error("Exception while uploading %s" % fname)
                raise
            return

        # Otherwise, save to local disk
        if not os.path.isdir(os.path.dirname(fname)):
            os.mkdir(os.path.dirname(fname))
        with open(fname, 'w') as f:
            f.write(out_str)

    def get_next_visit_id(self):
        """Generate visit id as randomly generated 64bit UUIDs
        """
        return (uuid.uuid4().int & (1 << 64) - 1) - 2**63

    def get_next_crawl_id(self):
        """Generate crawl id as randomly generated 32bit UUIDs

        Note: Parquet's partitioned dataset reader only supports integer
        partition columns up to 32 bits.
        """
        return (uuid.uuid4().int & (1 << 32) - 1) - 2**31

    def launch(self):
        """Launch the aggregator listener process"""
        super(ParquetAggregator, self).launch(
            listener_process_runner, self._instance_id)
