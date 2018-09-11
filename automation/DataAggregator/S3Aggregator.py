from __future__ import absolute_import, print_function

import json
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

from .BaseAggregator import BaseAggregator, BaseListener
from .parquet_schema import PQ_SCHEMAS

CACHE_SIZE = 500


def listener_process_runner(manager_params, status_queue, task_id):
    """SqliteListener runner. Pass to new process"""
    listener = S3Listener(status_queue, manager_params, task_id)
    listener.startup()

    while True:
        if listener.should_shutdown():
            break
        try:
            record = listener.record_queue.get(block=True, timeout=5)
            listener.process_record(record)
        except queue.Empty:
            pass

    listener.drain_queue()
    listener.shutdown()


class S3Listener(BaseListener):
    """Listener that pushes aggregated records to S3.

    Records for each page visit are stored in memory during a page visit. Once
    the browser moves to another page, the data is written to S3 as part of
    a parquet dataset. The schema for this dataset is given in
    ./parquet_schema.py
    """
    def __init__(self, status_queue, manager_params, task_id):
        self.dir = manager_params['s3_directory']
        self.browser_map = dict()  # maps crawl_id to visit_id
        self._records = dict()  # maps visit_id and table to records
        self._batches = dict()  # maps table_name to a list of batches
        self._task_id = task_id
        self._bucket = manager_params['s3_bucket']
        self._fs = s3fs.S3FileSystem()
        self._s3_bucket_uri = 's3://%s/%s/visits/%%s' % (
            self._bucket, self.dir)
        super(S3Listener, self).__init__(status_queue, manager_params)

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
            except pa.lib.ArrowInvalid as e:
                self.logger.error(
                    "Error while sending record:\n%s\n%s\n%s\n"
                    % (table_name, type(e), e)
                )
                pass
        del self._records[visit_id]

    def _send_to_s3(self, force=False):
        """Copy in-memory batches to s3"""
        for table_name, batches in self._batches.items():
            if not force and len(batches) <= CACHE_SIZE:
                continue
            try:
                table = pa.Table.from_batches(batches)
                pq.write_to_dataset(
                    table, self._s3_bucket_uri % table_name,
                    filesystem=self._fs,
                    preserve_index=False,
                    compression='snappy'
                )
            except pa.lib.ArrowInvalid as e:
                self.logger.error(
                    "Error while sending record:\n%s\n%s\n%s\n"
                    % (table_name, type(e), e)
                )
                pass
            del self._batches[table_name]

    def process_record(self, record):
        """Add `record` to database"""
        if len(record) != 2:
            self.logger.error("Query is not the correct length")
            return

        table, data = record
        if table == "create_table":  # drop these statements
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
            self._send_to_s3()
            self.browser_map[crawl_id] = visit_id

        # Convert data to text type
        for k, v in data.items():
            if isinstance(v, six.binary_type):
                data[k] = six.text_type(v, errors='ignore')
            elif callable(v):
                data[k] = six.text_type(v)

        # Save record to disk
        self._write_record(table, data, visit_id)

    def drain_queue(self):
        """Process remaining records in queue and sync final files to S3"""
        super(S3Listener, self).drain_queue()
        self._send_to_s3(force=True)


class S3Aggregator(BaseAggregator):
    """
    Receives data records from other processes and aggregates them locally
    per-site before pushing them to a remote S3 bucket. The remote files are
    saved in a Paquet Dataset partitioned by the crawl_id and visit_id of
    each record.

    The visit and task ids are randomly generated to allow multiple writers
    to write to the same S3 bucket. Every record should have a `visit_id`
    (which identifies the site visit) and a `crawl_id` (which identifies the
    browser instance) so we can associate records with the appropriate meta
    data. Any records which lack this information will be dropped by the
    writer.

    Note: Parquet's partitioned dataset reader only supports integer partition
    columns up to 32 bits. Thus, the visit_id is capped at 32 bits and might
    have collisions over the top million sites. As such, tables should be
    joined on the `crawl_id` and `visit_id`.
    """
    def __init__(self, manager_params, browser_params):
        super(S3Aggregator, self).__init__(manager_params, browser_params)
        self.dir = manager_params['s3_directory']
        self.bucket = manager_params['s3_bucket']
        self.s3 = boto3.client('s3')
        self._task_id = uuid.uuid4().int & (1 << 32) - 1
        self._create_bucket()

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
        fname = "%s/instance-%s_configuration.json" % (self.dir, self._task_id)

        # Config parameters for update
        out = dict()
        out['manager_params'] = self.manager_params
        out['openwpm_version'] = six.text_type(openwpm_version)
        out['browser_version'] = six.text_type(browser_version)
        out['browser_params'] = self.browser_params
        out_str = json.dumps(out)
        if type(out_str) != six.binary_type:
            out_str = six.binary_type(out_str, 'utf-8')
        out_f = six.BytesIO(out_str)

        # Upload to S3 and delete local copy
        try:
            self.s3.upload_fileobj(out_f, self.bucket, fname)
        except Exception:
            self.logger.error("Exception while uploading %s" % fname)
            raise

    def get_next_visit_id(self):
        """Generate visit id as randomly generated 32bit UUIDs
        """
        return uuid.uuid4().int & (1 << 32) - 1

    def get_next_crawl_id(self):
        """Generate crawl id as randomly generated 32bit UUIDs

        Note: Parquet's partitioned dataset reader only supports integer
        partition columns up to 32 bits.
        """
        return uuid.uuid4().int & (1 << 32) - 1

    def launch(self):
        """Launch the aggregator listener process"""
        super(S3Aggregator, self).launch(
            listener_process_runner, self._task_id)
