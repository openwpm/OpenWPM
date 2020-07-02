
import base64
import gzip
import hashlib
import io
import json
import queue
import random
import time
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, MutableSet, Optional

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import s3fs
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError
from pyarrow.filesystem import S3FSWrapper  # noqa

from .base import (RECORD_TYPE_CONTENT, RECORD_TYPE_CREATE,
                   RECORD_TYPE_SPECIAL, BaseAggregator, BaseListener,
                   BaseParams)
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


def listener_process_runner(base_params: BaseParams,
                            manager_params: Dict[str, Any],
                            instance_id: int) -> None:
    """S3Listener runner. Pass to new process"""
    listener = S3Listener(base_params, manager_params, instance_id)
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

    def __init__(self,
                 base_params: BaseParams,
                 manager_params: Dict[str, Any],
                 instance_id: int) -> None:
        self.dir = manager_params['s3_directory']
        self._bucket = manager_params['s3_bucket']
        self._s3_content_cache: MutableSet[str] = \
            set()  # cache of filenames already uploaded
        self._s3 = boto3.client('s3', config=S3_CONFIG)
        self._s3_resource = boto3.resource('s3', config=S3_CONFIG)
        self._fs = s3fs.S3FileSystem(
            session=boto3.DEFAULT_SESSION,
            config_kwargs=S3_CONFIG_KWARGS
        )
        self._s3_bucket_uri = 's3://%s/%s/visits/%%s' % (
            self._bucket, self.dir)
        # time last record was received
        self._last_record_received: Optional[float] = None
        super(S3Listener, self).__init__(*base_params)


    def _create_batch(self, visit_id: int) -> None:
        """Create record batches for all records from `visit_id`"""
        if visit_id not in self._records:
            # The batch for this `visit_id` was already created, skip
            return
        for table_name, data in self._records[visit_id].items():
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
        self._unsaved_visit_ids.add(visit_id)

    def _exists_on_s3(self, filename: str) -> bool:
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

    def run_visit_completion_tasks(self, visit_id: int,
                                   interrupted: bool = False):
        if interrupted:
            self.logger.error(
                "Visit with visit_id %d got interrupted", visit_id)
            self._write_record("incomplete_visits",
                               {"visit_id": visit_id}, visit_id)
            self._create_batch(visit_id)
            self.mark_visit_incomplete(visit_id)
            return
        self._create_batch(visit_id)
        self.commit_structured_records()

    def shutdown(self):
        # We should only have unsaved records if we are in forced shutdown
        if self._relaxed and self._records:
            self.logger.error("Had unfinished records during relaxed shutdown")
        super(S3Listener, self).shutdown()
        self.commit_structured_records(force=True)


"""
Methods for S3 Aggregator

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
    BaseAggregator.__init__(self, manager_params, browser_params)
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
    out_bytes = out_str.encode('utf-8')
    out_f = io.BytesIO(out_bytes)

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
    BaseAggregator.launch(
        listener_process_runner, self.manager_params, self._instance_id)
