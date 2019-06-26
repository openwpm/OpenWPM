from __future__ import absolute_import

import boto3
from localstack.services import infra

from ..automation import TaskManager
from .openwpmtest import OpenWPMTest
from .utilities import (BASE_TEST_URL, LocalS3Dataset, LocalS3Session,
                        local_s3_bucket)


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

    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        manager_params['output_format'] = 's3'
        manager_params['s3_bucket'] = local_s3_bucket(self.s3_resource)
        manager_params['s3_directory'] = 's3-aggregator-tests'
        browser_params[0]['http_instrument'] = True
        return manager_params, browser_params

    def test_s3_aggregation(self, tmpdir):
        TEST_SITE = "%s/http_test_page.html" % BASE_TEST_URL

        # Run the test crawl
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get(TEST_SITE)
        manager.close()

        dataset = LocalS3Dataset(
            manager_params['s3_bucket'],
            manager_params['s3_directory']
        )
        requests = dataset.load_table('http_requests')

        assert TEST_SITE in requests.top_level_url.unique()
