
import logging
import os
import time

import pytest

from ..automation import MPLogger
from ..automation.utilities.multiprocess_utils import Process
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
NAMED_LOGGER_INFO_1 = 'Named Logger 1 Parent - INFO'
NAMED_LOGGER_INFO_2 = 'Named Logger 2 Parent - INFO'
logger = logging.getLogger('openwpm')


def child_proc(index):
    logger = logging.getLogger('openwpm')
    logger.info(CHILD_INFO_STR_1 % index)
    logger.info(CHILD_INFO_STR_2 % index)
    logger.debug(CHILD_DEBUG_STR % index)
    time.sleep(1)
    logger.error(CHILD_ERROR_STR % index)
    logger.critical(CHILD_CRITICAL_STR % index)
    logger.warning(CHILD_WARNING_STR % index)
    return


def child_proc_with_exception(index):
    def test_func():
        print("test")

    class TestClass(object):
        def __init__(self):
            return

        def test_method(self):
            return

    class TestSubClass(TestClass):
        def test_method(self):
            print("test method")
            return

    logger = logging.getLogger('openwpm')
    logger.info(CHILD_INFO_STR_1 % index)
    logger.info(CHILD_INFO_STR_2 % index)
    test_class = TestClass()
    test_subclass = TestSubClass()
    raise IOError(
        CHILD_EXCEPTION_STR % index,
        ('blah', 1, test_func, test_class, test_subclass,
         TestClass, TestSubClass)
    )


def child_proc_logging_exception():
    logger = logging.getLogger('openwpm')
    try:
        raise Exception("This is my generic Test Exception")
    except Exception:
        logger.error(
            "I'm logging an exception", exc_info=True,
        )


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

        child_process_1 = Process(
            target=child_proc,
            args=(0,)
        )
        child_process_1.daemon = True
        child_process_1.start()
        child_process_2 = Process(
            target=child_proc,
            args=(1,)
        )
        child_process_2.daemon = True
        child_process_2.start()

        # Send some sample logs
        logger.info(PARENT_INFO_STR_1)
        logger.error(PARENT_ERROR_STR)
        logger.critical(PARENT_CRITICAL_STR)
        logger.debug(PARENT_DEBUG_STR)
        logger.warning(PARENT_WARNING_STR)

        logger1 = logging.getLogger('test1')
        logger2 = logging.getLogger('test2')
        logger1.info(NAMED_LOGGER_INFO_1)
        logger2.info(NAMED_LOGGER_INFO_2)

        # Close the logging server
        time.sleep(2)  # give some time for logs to be sent
        openwpm_logger.close()
        child_process_1.join()
        child_process_2.join()
        print("Child processes joined...")

        log_content = self.get_logfile_contents(log_file)
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

    @pytest.mark.skipif(
        "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
        reason='Flaky on Travis CI')
    def test_child_process_with_exception(self, tmpdir):
        log_file = self.get_logfile_path(str(tmpdir))
        openwpm_logger = MPLogger.MPLogger(log_file)

        child_process_1 = Process(
            target=child_proc_with_exception,
            args=(0,)
        )
        child_process_1.daemon = True
        child_process_1.start()
        child_process_2 = Process(
            target=child_proc_with_exception,
            args=(1,)
        )
        child_process_2.daemon = True
        child_process_2.start()

        # Close the logging server
        time.sleep(2)  # give some time for logs to be sent
        child_process_1.join()
        child_process_2.join()
        print("Child processes joined...")
        openwpm_logger.close()

        log_content = self.get_logfile_contents(log_file)
        for child in range(2):
            assert(log_content.count(CHILD_INFO_STR_1 % child) == 1)
            assert(log_content.count(CHILD_INFO_STR_2 % child) == 1)
            assert(log_content.count(CHILD_EXCEPTION_STR % child) == 1)

    @pytest.mark.skipif(
        "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
        reason='Flaky on Travis CI')
    def test_child_process_logging(self, tmpdir):
        log_file = self.get_logfile_path(str(tmpdir))
        openwpm_logger = MPLogger.MPLogger(log_file)
        child_process = Process(target=child_proc_logging_exception())
        child_process.daemon = True
        child_process.start()
        openwpm_logger.close()
        child_process.join()
        log_content = self.get_logfile_contents(log_file)
        assert ("I'm logging an exception" in log_content)
