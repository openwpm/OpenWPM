
import json
import time
from collections import defaultdict

import boto3
import pytest
from localstack.services import infra

from ..automation import TaskManager
from ..automation.DataAggregator.parquet_schema import PQ_SCHEMAS
from .openwpmtest import OpenWPMTest
from .utilities import (BASE_TEST_URL, LocalS3Dataset, LocalS3Session,
                        local_s3_bucket)

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


class TestS3Aggregator(OpenWPMTest):

    @classmethod
    def setup_class(self):
        infra.start_infra(asynchronous=True, apis=["s3"])
        boto3.DEFAULT_SESSION = LocalS3Session()
        self.s3_client = boto3.client('s3')
        self.s3_resource = boto3.resource('s3')

    @classmethod
    def teardown_class(self):
        infra.stop_infra()

    def get_config(self, num_browsers=1, data_dir=""):
        manager_params, browser_params = self.get_test_config(
            data_dir, num_browsers=num_browsers)
        manager_params['output_format'] = 's3'
        manager_params['s3_bucket'] = local_s3_bucket(self.s3_resource)
        manager_params['s3_directory'] = 's3-aggregator-tests'
        for i in range(num_browsers):
            browser_params[i]['http_instrument'] = True
            browser_params[i]['js_instrument'] = True
            browser_params[i]['cookie_instrument'] = True
            browser_params[i]['navigation_instrument'] = True
            browser_params[i]['callstack_instrument'] = True
        return manager_params, browser_params

    def test_basic_properties(self):
        TEST_SITE = "%s/s3_aggregator.html" % BASE_TEST_URL
        NUM_VISITS = 2
        NUM_BROWSERS = 4
        manager_params, browser_params = self.get_config(
            num_browsers=NUM_BROWSERS)
        manager = TaskManager.TaskManager(manager_params, browser_params)
        for _ in range(NUM_VISITS * NUM_BROWSERS):
            manager.get(TEST_SITE, sleep=1)
        manager.close()

        dataset = LocalS3Dataset(
            manager_params['s3_bucket'],
            manager_params['s3_directory']
        )

        # Test visit_id consistency
        visit_ids = defaultdict(set)
        for table_name in PQ_SCHEMAS:
            # flash cookie instrumentation not enabled
            if table_name == 'flash_cookies':
                continue
            table = dataset.load_table(table_name)
            visit_ids[table_name] = table.visit_id.unique()
            assert len(visit_ids[table_name]) == NUM_VISITS * NUM_BROWSERS
            for vid in visit_ids[table_name]:
                assert(vid >= 0) and (vid < (1 << 53))
        for table_name, ids in visit_ids.items():
            assert set(ids) == set(visit_ids['site_visits'])

        # Ensure http table is created
        assert TEST_SITE in dataset.load_table(
            'http_requests').top_level_url.unique()

        # Ensure config directory is created and contains the correct number
        # of configuration files
        config_file = dataset.list_files('config', prepend_root=True)
        assert len(config_file) == 1  # only one instance started in test
        config = json.loads(str(
            dataset.get_file(config_file[0]), 'utf-8'))
        assert len(config['browser_params']) == NUM_BROWSERS

    def test_commit_on_timeout(self):
        TEST_SITE = "%s/s3_aggregator.html" % BASE_TEST_URL
        manager_params, browser_params = self.get_config(num_browsers=1)
        manager_params['s3_directory'] = 's3-aggregator-tests-2'
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get(TEST_SITE, sleep=1)
        dataset = LocalS3Dataset(
            manager_params['s3_bucket'],
            manager_params['s3_directory']
        )
        with pytest.raises((FileNotFoundError, OSError)):
            requests = dataset.load_table('http_requests')
        time.sleep(45)  # Current timeout
        dataset2 = LocalS3Dataset(
            manager_params['s3_bucket'],
            manager_params['s3_directory']
        )
        requests = dataset2.load_table('http_requests')
        assert TEST_SITE in requests.top_level_url.unique()
        manager.close()
