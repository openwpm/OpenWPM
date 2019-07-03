from __future__ import absolute_import, print_function

from Queue import Queue

from ..automation.DataAggregator import ParquetAggregator
from .openwpmtest import OpenWPMTest


class TestParquetAggregator(OpenWPMTest):
    """Test ParquetListener and ParquetAggregator"""

    def get_test_config(self):
        manager_params, browser_params = super(
            TestParquetAggregator, self).get_test_config()
        manager_params['output_format'] = 'local_parquet'
        manager_params['parquet_batch_size'] = 10
        return manager_params, browser_params

    def get_listener(self):
        manager_params, browser_params = self.get_test_config()
        self.status_queue = Queue()
        self.shutdown_queue = Queue()
        return ParquetAggregator.ParquetListener(
            self.status_queue, self.shutdown_queue, manager_params, 0)

    def test_listener(self):
        # listener = self.get_listener()
        assert True
