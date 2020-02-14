
import base64
import gzip
import hashlib
import io
import json
import queue
import random
import time
from collections import defaultdict

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import s3fs
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError
from pyarrow.filesystem import S3FSWrapper  # noqa

from .BaseAggregator import RECORD_TYPE_CONTENT, BaseAggregator, BaseListener
from .parquet_schema import PQ_SCHEMAS

CACHE_SIZE = 500
SITE_VISITS_INDEX = '_site_visits_index'
CONTENT_DIRECTORY = 'content'
CONFIG_DIR = 'config'
BATCH_COMMIT_TIMEOUT = 30  # commit a batch if no new records for N seconds
S3_CONFIG_KWARGS = {
    'retries': {
        'max_attempts': 20
    }
}
S3_CONFIG = Config(**S3_CONFIG_KWARGS)


def listener_process_runner(
        manager_params, status_queue, shutdown_queue, instance_id):
    """S3Listener runner. Pass to new process"""
    listener = S3Listener(
        status_queue, shutdown_queue, manager_params, instance_id)
    listener.startup()

    while True:
        listener.update_status_queue()
        listener.save_batch_if_past_timeout()
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

    def __init__(
            self, status_queue, shutdown_queue, manager_params, instance_id):
        self.dir = manager_params['s3_directory']
        self.browser_map = dict()  # maps crawl_id to visit_id
        self._records = dict()  # maps visit_id and table to records
        self._batches = dict()  # maps table_name to a list of batches
        self._instance_id = instance_id
        self._bucket = manager_params['s3_bucket']
        self._s3_content_cache = set()  # cache of filenames already uploaded
        self._s3 = boto3.client('s3', config=S3_CONFIG)
        self._s3_resource = boto3.resource('s3', config=S3_CONFIG)
        self._fs = s3fs.S3FileSystem(
            session=boto3.DEFAULT_SESSION,
            config_kwargs=S3_CONFIG_KWARGS
        )
        self._s3_bucket_uri = 's3://%s/%s/visits/%%s' % (
            self._bucket, self.dir)
        self._last_record_received = None  # time last record was received
        super(S3Listener, self).__init__(
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
        if visit_id not in self._records:
            # The batch for this `visit_id` was already created, skip
            return
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
            except pa.lib.ArrowInvalid:
                self.logger.error(
                    "Error while creating record batch for table %s\n"
                    % table_name, exc_info=True
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
        # Check local filename cache
        if filename.split('/', 1)[1] in self._s3_content_cache:
            self.logger.debug(
                "File `%s` found in content cache." % filename)
            return True

        # Check S3
        try:
            self._s3_resource.Object(self._bucket, filename).load()
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise
        except EndpointConnectionError:
            self.logger.error(
                "Exception while checking if file exists %s" % filename,
                exc_info=True
            )
            return False

        # Add filename to local cache to avoid remote lookups on next request
        # We strip the bucket name as its the same for all files
        self._s3_content_cache.add(filename.split('/', 1)[1])
        return True

    def _write_str_to_s3(self, string, filename,
                         compressed=True, skip_if_exists=True):
        """Write `string` data to S3 with name `filename`"""
        if skip_if_exists and self._exists_on_s3(filename):
            self.logger.debug(
                "File `%s` already exists on s3, skipping..." % filename)
            return
        if not isinstance(string, bytes):
            string = string.encode('utf-8')
        if compressed:
            out_f = io.BytesIO()
            with gzip.GzipFile(fileobj=out_f, mode='w') as writer:
                writer.write(string)
            out_f.seek(0)
        else:
            out_f = io.BytesIO(string)

        # Upload to S3
        try:
            self._s3.upload_fileobj(out_f, self._bucket, filename)
            self.logger.debug(
                "Successfully uploaded file `%s` to S3." % filename)
            # Cache the filenames that are already on S3
            # We strip the bucket name as its the same for all files
            if skip_if_exists:
                self._s3_content_cache.add(filename.split('/', 1)[1])
        except Exception:
            self.logger.error(
                "Exception while uploading %s" % filename, exc_info=True
            )
            pass

    def _send_to_s3(self, force=False):
        """Copy in-memory batches to s3"""
        for table_name, batches in self._batches.items():
            if not force and len(batches) <= CACHE_SIZE:
                continue
            if table_name == SITE_VISITS_INDEX:
                out_str = '\n'.join([json.dumps(x) for x in batches])
                if not isinstance(out_str, bytes):
                    out_str = out_str.encode('utf-8')
                fname = '%s/site_index/instance-%s-%s.json.gz' % (
                    self.dir, self._instance_id,
                    hashlib.md5(out_str).hexdigest()
                )
                self._write_str_to_s3(out_str, fname)
            else:
                if len(batches) == 0:
                    continue
                try:
                    table = pa.Table.from_batches(batches)
                    pq.write_to_dataset(
                        table, self._s3_bucket_uri % table_name,
                        filesystem=self._fs,
                        partition_cols=['instance_id'],
                        compression='snappy',
                        flavor='spark'
                    )
                except (pa.lib.ArrowInvalid, EndpointConnectionError):
                    self.logger.error(
                        "Error while sending records for: %s" % table_name,
                        exc_info=True
                    )
                    pass
            self._batches[table_name] = list()

    def save_batch_if_past_timeout(self):
        """Save the current batch of records if no new data has been received.

        If we aren't receiving new data for this batch we commit early
        regardless of the current batch size."""
        if self._last_record_received is None:
            return
        if time.time() - self._last_record_received < BATCH_COMMIT_TIMEOUT:
            return
        self.logger.debug(
            "Saving current record batches to S3 since no new data has "
            "been written for %d seconds." %
            (time.time() - self._last_record_received)
        )
        self.drain_queue()
        self._last_record_received = None

    def process_record(self, record):
        """Add `record` to database"""
        if len(record) != 2:
            self.logger.error("Query is not the correct length")
            return
        self._last_record_received = time.time()
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
            self._send_to_s3()
            self.browser_map[crawl_id] = visit_id

        # Convert data to text type
        for k, v in data.items():
            if isinstance(v, bytes):
                data[k] = str(v, errors='ignore')
            elif callable(v):
                data[k] = str(v)
            # TODO: Can we fix this in the extension?
            elif type(v) == dict:
                data[k] = json.dumps(v)

        # Save record to disk
        self._write_record(table, data, visit_id)

    def process_content(self, record):
        """Upload page content `record` to S3"""
        if record[0] != RECORD_TYPE_CONTENT:
            raise ValueError(
                "Incorrect record type passed to `process_content`. Expected "
                "record of type `%s`, received `%s`." % (
                    RECORD_TYPE_CONTENT, record[0])
            )
        content, content_hash = record[1]
        content = base64.b64decode(content)
        fname = "%s/%s/%s.gz" % (self.dir, CONTENT_DIRECTORY, content_hash)
        self._write_str_to_s3(content, fname)

    def drain_queue(self):
        """Process remaining records in queue and sync final files to S3"""
        super(S3Listener, self).drain_queue()
        for visit_id in self.browser_map.values():
            self._create_batch(visit_id)
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
    columns up to 32 bits. Currently, `instance_id` is the only partition
    column, and thus can be no larger than 32 bits.
    """

    def __init__(self, manager_params, browser_params):
        super(S3Aggregator, self).__init__(manager_params, browser_params)
        self.dir = manager_params['s3_directory']
        self.bucket = manager_params['s3_bucket']
        self.s3 = boto3.client('s3')
        self._instance_id = random.getrandbits(32)
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
        fname = "%s/%s/instance-%s_configuration.json" % (
            self.dir, CONFIG_DIR, self._instance_id)

        # Config parameters for update
        out = dict()
        out['manager_params'] = self.manager_params
        out['openwpm_version'] = str(openwpm_version)
        out['browser_version'] = str(browser_version)
        out['browser_params'] = self.browser_params
        out_str = json.dumps(out)
        if not isinstance(out_str, bytes):
            out_str = out_str.encode('utf-8')
        out_f = io.BytesIO(out_str)

        # Upload to S3 and delete local copy
        try:
            self.s3.upload_fileobj(out_f, self.bucket, fname)
        except Exception:
            self.logger.error("Exception while uploading %s" % fname)
            raise

    def get_next_visit_id(self):
        """Generate visit id as randomly generated positive integer less than 2^53.

        Parquet can support integers up to 64 bits, but Javascript can only
        represent integers up to 53 bits:
        https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER
        Thus, we cap these values at 53 bits.
        """
        return random.getrandbits(53)

    def get_next_crawl_id(self):
        """Generate crawl id as randomly generated positive 32bit integer

        Note: Parquet's partitioned dataset reader only supports integer
        partition columns up to 32 bits.
        """
        return random.getrandbits(32)

    def launch(self):
        """Launch the aggregator listener process"""
        super(S3Aggregator, self).launch(
            listener_process_runner, self._instance_id)
