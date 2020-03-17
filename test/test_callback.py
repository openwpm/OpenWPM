from functools import partial
from typing import List

import boto3
from localstack.services import infra
from multiprocess import Queue

from ..automation.CommandSequence import CommandSequence
from ..automation.TaskManager import TaskManager
from .openwpmtest import OpenWPMTest
from .utilities import (BASE_TEST_URL, LocalS3Dataset, LocalS3Session,
                        local_s3_bucket)


class TestCallbackCommand(OpenWPMTest):
    """Test test the Aggregators as well as the entire callback machinery
       to see if all callbacks get correctly called"""

    @classmethod
    def setup_class(cls):
        infra.start_infra(asynchronous=True, apis=["s3"])
        boto3.DEFAULT_SESSION = LocalS3Session()
        cls.s3_client = boto3.client('s3')
        cls.s3_resource = boto3.resource('s3')

    @classmethod
    def teardown_class(cls):
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

    def test_local_callbacks(self):
        manager_params, browser_params = self.get_config()
        TEST_SITE = BASE_TEST_URL + "/test_pages/simple_a.html"
        manager = TaskManager(manager_params, browser_params)

        def callback(argument: List[int]):
            argument.extend([1, 2, 3])

        my_list = []
        sequence = CommandSequence(TEST_SITE, reset=True,
                                   blocking=True,
                                   callback=partial(callback, my_list))
        sequence.get()

        manager.execute_command_sequence(sequence)
        manager.close()
        assert my_list == [1, 2, 3]

    def test_s3_callbacks(self):
        TEST_SITE = BASE_TEST_URL + "/test_pages/simple_a.html"
        manager_params, browser_params = self.get_config()
        dataset = LocalS3Dataset(
            manager_params['s3_bucket'],
            manager_params['s3_directory']
        )
        manager = TaskManager(manager_params, browser_params)
        queue = Queue()

        def ensure_site_in_s3():
            # Ensure http table is created
            queue.put(TEST_SITE in dataset.load_table(
                'http_requests').top_level_url.unique())

        sequence = CommandSequence(TEST_SITE, reset=True,
                                   blocking=True,
                                   callback=ensure_site_in_s3)
        sequence.get()
        manager.execute_command_sequence(sequence)
        manager.close()

        assert queue.get()
