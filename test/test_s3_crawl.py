from __future__ import absolute_import

import os
import tarfile

import pytest
from six.moves.urllib.parse import urlparse

from ..automation import TaskManager
from ..automation.utilities import db_utils, domain_utils
from .openwpmtest import OpenWPMTest

from .utilities import local_s3_bucket, download_s3_directory

TEST_SITES = [
    'http://example.com'
]

psl = domain_utils.get_psl()


class TestS3Crawl(OpenWPMTest):
    """ Runs a short test crawl.

    This should be used to test any features that require real
    crawl data. This should be avoided if possible, as controlled
    tests will be easier to debug
    """

    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        # Requires that `SERVICES=s3 localstack start` has been started
        manager_params['output_format'] = 's3'
        manager_params['s3_bucket'] = local_s3_bucket()
        manager_params['s3_directory'] = 'demo-local-s3'
        browser_params[0]['profile_archive_dir'] =\
            os.path.join(manager_params['data_directory'], 'browser_profile')
        browser_params[0]['http_instrument'] = True
        return manager_params, browser_params

    @pytest.mark.slow
    def test_minimal_crawl_with_s3_aggregation(self, tmpdir):
        # Run the test crawl
        data_dir = os.path.join(str(tmpdir), 'data_dir')
        manager_params, browser_params = self.get_config(data_dir)
        manager = TaskManager.TaskManager(manager_params, browser_params)
        for site in TEST_SITES:
            manager.get(site)
        manager.close()

        # Copy the resulting S3 contents to ./local-s3-data
        print("Copying the resulting S3 contents...")
        destination = os.path.join(data_dir, 'local-s3-data')
        download_s3_directory(
            manager_params['s3_directory'],
            destination,
            manager_params['s3_bucket'])
        print("Copied the resulting S3 contents to %s" % destination)

        # TODO
        assert True
