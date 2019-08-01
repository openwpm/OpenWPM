from __future__ import absolute_import

import logging
import os
import time

import multiprocess as mp

from ..automation import MPLogger
from .openwpmtest import OpenWPMTest

CHILD_INFO_STR_1 = 'Child %d - INFO1'
CHILD_INFO_STR_2 = 'Child %d - INFO2'
CHILD_DEBUG_STR = 'Child %d - DEBUG'
CHILD_ERROR_STR = 'Child %d - ERROR'
CHILD_CRITICAL_STR = 'Child %d - CRITICAL'
CHILD_WARNING_STR = 'Child %d - WARNING'
CHILD_EXCEPTION_STR = 'Child %d - Test Exception!'
PARENT_INFO_STR_1 = 'Parent - INFO1'
PARENT_INFO_STR_2 = 'Parent - INFO2'
PARENT_DEBUG_STR = 'Parent - DEBUG'
PARENT_ERROR_STR = 'Parent - ERROR'
PARENT_CRITICAL_STR = 'Parent - CRITICAL'
PARENT_WARNING_STR = 'Parent - WARNING'
PARENT_EXCEPTION_STR = 'Parent - Test Exception!'


def child_proc(index):
    logging.info(CHILD_INFO_STR_1 % index)
    logging.info(CHILD_INFO_STR_2 % index)
    logging.debug(CHILD_DEBUG_STR % index)
    time.sleep(1)
    logging.error(CHILD_ERROR_STR % index)
    logging.critical(CHILD_CRITICAL_STR % index)
    logging.warning(CHILD_WARNING_STR % index)
    return


def child_proc_with_exception(index):
    logging.info(CHILD_INFO_STR_1 % index)
    logging.info(CHILD_INFO_STR_2 % index)
    raise RuntimeError(CHILD_EXCEPTION_STR)


class TestMPLogger(OpenWPMTest):

    def get_logfile_path(self, directory):
        return os.path.join(directory, 'mplogger.log')

    def get_logfile_contents(self, logfile):
        with open(logfile, 'r') as f:
            content = f.read().strip()
        return content

    def test_multiprocess(self, tmpdir):
        # Set up loggingserver
        log_file = self.get_logfile_path(str(tmpdir))
        openwpm_logger = MPLogger.MPLogger(log_file)

        child_process_1 = mp.Process(
            target=child_proc,
            args=(0,)
        )
        child_process_1.daemon = True
        child_process_1.start()
        child_process_2 = mp.Process(
            target=child_proc,
            args=(1,)
        )
        child_process_2.daemon = True
        child_process_2.start()

        # Send some sample logs
        logging.info(PARENT_INFO_STR_1)
        logging.error(PARENT_ERROR_STR)
        logging.critical(PARENT_CRITICAL_STR)
        logging.debug(PARENT_DEBUG_STR)
        logging.warning(PARENT_WARNING_STR)

        logger1 = logging.getLogger('test1')
        logger2 = logging.getLogger('test2')
        logger1.info('asdfasdfsa')
        logger2.info('1234567890')

        # Close the logging server
        time.sleep(2)  # give some time for logs to be sent
        openwpm_logger.close()
        child_process_1.join()
        child_process_2.join()
        print("Server closed, exiting...")

        log_content = self.get_logfile_contents(log_file)
        print(log_content)
        for child in range(2):
            assert(log_content.count(CHILD_INFO_STR_1 % child) == 1)
            assert(log_content.count(CHILD_INFO_STR_2 % child) == 1)
            assert(log_content.count(CHILD_ERROR_STR % child) == 1)
            assert(log_content.count(CHILD_CRITICAL_STR % child) == 1)
            assert(log_content.count(CHILD_DEBUG_STR % child) == 1)
            assert(log_content.count(CHILD_WARNING_STR % child) == 1)
        assert(log_content.count(PARENT_INFO_STR_1) == 1)
        assert(log_content.count(PARENT_ERROR_STR) == 1)
        assert(log_content.count(PARENT_CRITICAL_STR) == 1)
        assert(log_content.count(PARENT_DEBUG_STR) == 1)
        assert(log_content.count(PARENT_WARNING_STR) == 1)

    def test_multiple_instances(self, tmpdir):
        os.makedirs(str(tmpdir) + '-1')
        self.test_multiprocess(str(tmpdir) + '-1')
        os.makedirs(str(tmpdir) + '-2')
        self.test_multiprocess(str(tmpdir) + '-2')
