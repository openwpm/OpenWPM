import logging
import os
import time

from openwpm.telemetry import setup_telemetry, shutdown_telemetry
from openwpm.utilities.multiprocess_utils import Process

CHILD_INFO_STR_1 = "Child %d - INFO1"
CHILD_INFO_STR_2 = "Child %d - INFO2"
CHILD_DEBUG_STR = "Child %d - DEBUG"
CHILD_ERROR_STR = "Child %d - ERROR"
CHILD_CRITICAL_STR = "Child %d - CRITICAL"
CHILD_WARNING_STR = "Child %d - WARNING"
PARENT_INFO_STR_1 = "Parent - INFO1"
PARENT_INFO_STR_2 = "Parent - INFO2"
PARENT_DEBUG_STR = "Parent - DEBUG"
PARENT_ERROR_STR = "Parent - ERROR"
PARENT_CRITICAL_STR = "Parent - CRITICAL"
PARENT_WARNING_STR = "Parent - WARNING"
logger = logging.getLogger("openwpm")


def child_proc(index):
    logger = logging.getLogger("openwpm")
    logger.info(CHILD_INFO_STR_1 % index)
    logger.info(CHILD_INFO_STR_2 % index)
    logger.debug(CHILD_DEBUG_STR % index)
    time.sleep(1)
    logger.error(CHILD_ERROR_STR % index)
    logger.critical(CHILD_CRITICAL_STR % index)
    logger.warning(CHILD_WARNING_STR % index)
    return


def get_logfile_path(directory):
    return os.path.join(directory, "mplogger.log")


def get_logfile_contents(logfile):
    with open(logfile, "r") as f:
        content = f.read().strip()
    return content


def test_multiprocess(tmpdir):
    log_file = get_logfile_path(str(tmpdir))
    setup_telemetry(log_file)

    child_process_1 = Process(target=child_proc, args=(0,))
    child_process_1.daemon = True
    child_process_1.start()
    child_process_2 = Process(target=child_proc, args=(1,))
    child_process_2.daemon = True
    child_process_2.start()

    # Send some sample logs
    logger.info(PARENT_INFO_STR_1)
    logger.error(PARENT_ERROR_STR)
    logger.critical(PARENT_CRITICAL_STR)
    logger.debug(PARENT_DEBUG_STR)
    logger.warning(PARENT_WARNING_STR)

    # Close the logging server
    time.sleep(2)  # give some time for logs to be sent
    child_process_1.join()
    child_process_2.join()
    print("Child processes joined...")
    shutdown_telemetry()

    log_content = get_logfile_contents(log_file)
    # Parent logs should always be present
    assert log_content.count(PARENT_INFO_STR_1) == 1
    assert log_content.count(PARENT_ERROR_STR) == 1
    assert log_content.count(PARENT_CRITICAL_STR) == 1
    assert log_content.count(PARENT_DEBUG_STR) == 1
    assert log_content.count(PARENT_WARNING_STR) == 1


def test_multiple_instances(tmpdir):
    os.makedirs(str(tmpdir) + "-1")
    test_multiprocess(str(tmpdir) + "-1")
    os.makedirs(str(tmpdir) + "-2")
    test_multiprocess(str(tmpdir) + "-2")
