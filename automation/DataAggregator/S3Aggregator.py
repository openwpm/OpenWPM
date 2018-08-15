from __future__ import absolute_import, print_function

import glob
import json
import os
import Queue
import uuid

import boto3
import six
from botocore.exceptions import ClientError

from .BaseAggregator import BaseAggregator, BaseListener


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
        except Queue.Empty:
            pass

    listener.drain_queue()
    listener.shutdown()


class S3Listener(BaseListener):
    """Listener that pushes aggregated records to S3.

    Records for each page visit are saved locally in a json file while the page
    visit is still running. Once the browser moves to another page, the local
    file is reflected to S3 and removed from disk.
    """
    def __init__(self, status_queue, manager_params, task_id):
        self.dir = manager_params['data_directory']
        self.bucket = manager_params['s3_bucket']
        self.browser_map = dict()  # maps crawl_id to visit_id
        self.s3 = boto3.client('s3')
        self._task_id = task_id
        super(S3Listener, self).__init__(status_queue, manager_params)

    def _get_file_path(self, visit_id, table):
        """Get file handle corresponding to the given `visit_id`"""
        fname = "%s-%s-%s.json" % (self._task_id, visit_id, table)
        outfile = os.path.join(self.dir, fname)
        return outfile

    def _write_record(self, table, data, visit_id):
        """Write data to local file on disk"""
        with open(self._get_file_path(visit_id, table), 'a') as f:
            f.write(json.dumps(data) + '\n')

    def _send_to_s3(self, visit_id):
        """Copy local file to s3 and remove from disk"""
        pattern = "%s-%s-*.json" % (self._task_id, visit_id)
        for fname in glob.glob(os.path.join(self.dir, pattern)):
            try:
                key = os.path.basename(fname)
                self.s3.upload_file(fname, self.bucket, key)
            except Exception:
                self.logger.error("Exception while uploading %s" % fname)
                return
            os.remove(fname)

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
            return

        # Check if the browser for this record has moved on to a new visit
        if crawl_id not in self.browser_map:
            self.browser_map[crawl_id] = visit_id
        elif self.browser_map[crawl_id] != visit_id:
            self._send_to_s3(self.browser_map[crawl_id])
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
        for visit_id in self.browser_map.values():
            self._send_to_s3(visit_id)


class S3Aggregator(BaseAggregator):
    """
    Receives data records from other processes and aggregates them locally
    per-site before pushing them to a remote S3 bucket. The local files are
    deleted following a successful upload. Files are keyed by the
    run, visit, and data type. The output format is:
        `<task_id>_<visit_id>_<data_type>.json`
    for example:
        2_823342345_http_requests.json

    The visit and task ids are randomly generated to allow multiple writers
    to write to the same S3 bucket.
    """
    def __init__(self, manager_params, browser_params):
        super(S3Aggregator, self).__init__(manager_params, browser_params)
        if not os.path.exists(manager_params['data_directory']):
            os.mkdir(manager_params['data_directory'])
        self.dir = manager_params['data_directory']
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
        fname = "%s-crawl_configuration.json" % self._task_id
        fpath = os.path.join(self.dir, fname)

        # Write config parameters to disk
        out = dict()
        out['manager_params'] = self.manager_params
        out['openwpm_version'] = openwpm_version
        out['browser_version'] = browser_version
        out['browser_params'] = self.browser_params
        with open(os.path.join(self.dir, fname), 'w') as f:
            json.dump(out, f)

        # Upload to S3 and delete local copy
        try:
            self.s3.upload_file(fpath, self.bucket, fname)
        except Exception:
            self.logger.error("Exception while uploading %s" % fpath)
            raise
        os.remove(fpath)

    def get_next_visit_id(self):
        """Generate visit id as randomly generated 64bit UUIDs"""
        return uuid.uuid4().int & (1 << 64) - 1

    def get_next_crawl_id(self):
        """Generate crawl id as randomly generated 32bit UUIDs"""
        return uuid.uuid4().int & (1 << 32) - 1

    def launch(self):
        """Launch the aggregator listener process"""
        super(S3Aggregator, self).launch(
            listener_process_runner, self._task_id)
