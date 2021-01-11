import json
import logging
import os
import signal
import sys
import time
from threading import Lock
from typing import Any, Callable, List

import boto3
import sentry_sdk

from openwpm.command_sequence import CommandSequence
from openwpm.config import BrowserParams, ManagerParams
from openwpm.mp_logger import parse_config_from_env
from openwpm.task_manager import TaskManager
from openwpm.utilities import rediswq
from test.utilities import LocalS3Session, local_s3_bucket

# Configuration via environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis-box")
REDIS_QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "crawl-queue")
CRAWL_DIRECTORY = os.getenv("CRAWL_DIRECTORY", "crawl-data")
S3_BUCKET = os.getenv("S3_BUCKET", "openwpm-crawls")
DISPLAY_MODE = os.getenv("DISPLAY_MODE", "headless")
HTTP_INSTRUMENT = os.getenv("HTTP_INSTRUMENT", "1") == "1"
COOKIE_INSTRUMENT = os.getenv("COOKIE_INSTRUMENT", "1") == "1"
NAVIGATION_INSTRUMENT = os.getenv("NAVIGATION_INSTRUMENT", "1") == "1"
JS_INSTRUMENT = os.getenv("JS_INSTRUMENT", "1") == "1"
CALLSTACK_INSTRUMENT = os.getenv("CALLSTACK_INSTRUMENT", "1") == "1"
JS_INSTRUMENT_SETTINGS = os.getenv(
    "JS_INSTRUMENT_SETTINGS", '["collection_fingerprinting"]'
)
SAVE_CONTENT = os.getenv("SAVE_CONTENT", "")
PREFS = os.getenv("PREFS", None)
DWELL_TIME = int(os.getenv("DWELL_TIME", "10"))
TIMEOUT = int(os.getenv("TIMEOUT", "60"))
SENTRY_DSN = os.getenv("SENTRY_DSN", None)
LOGGER_SETTINGS = parse_config_from_env()
MAX_JOB_RETRIES = int(os.getenv("MAX_JOB_RETRIES", "2"))

JS_INSTRUMENT_SETTINGS = json.loads(JS_INSTRUMENT_SETTINGS)

if CALLSTACK_INSTRUMENT is True:
    # Must have JS_INSTRUMENT True for CALLSTACK_INSTRUMENT to work
    JS_INSTRUMENT = True

EXTENDED_LEASE_TIME = 2 * (TIMEOUT + DWELL_TIME + 30)

# Loads the default manager params
# We can't use more than one browser per instance because the job management
# code below requires blocking commands. For more context see:
# https://github.com/mozilla/OpenWPM/issues/470
NUM_BROWSERS = 1
manager_params = ManagerParams()
browser_params = [BrowserParams() for _ in range(NUM_BROWSERS)]

# Browser configuration
for i in range(NUM_BROWSERS):
    browser_params[i].display_mode = DISPLAY_MODE
    browser_params[i].http_instrument = HTTP_INSTRUMENT
    browser_params[i].cookie_instrument = COOKIE_INSTRUMENT
    browser_params[i].navigation_instrument = NAVIGATION_INSTRUMENT
    browser_params[i].callstack_instrument = CALLSTACK_INSTRUMENT
    browser_params[i].js_instrument = JS_INSTRUMENT
    browser_params[i].js_instrument_settings = JS_INSTRUMENT_SETTINGS
    if SAVE_CONTENT == "1":
        browser_params[i].save_content = True
    elif SAVE_CONTENT == "0":
        browser_params[i].save_content = False
    else:
        browser_params[i].save_content = SAVE_CONTENT
    if PREFS:
        browser_params[i].prefs = json.loads(PREFS)

# Manager configuration
manager_params.data_directory = "~/Desktop/%s/" % CRAWL_DIRECTORY
manager_params.log_directory = "~/Desktop/%s/" % CRAWL_DIRECTORY
manager_params.output_format = "s3"
manager_params.s3_bucket = S3_BUCKET
manager_params.s3_directory = CRAWL_DIRECTORY

# Allow the use of localstack's mock s3 service
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
if S3_ENDPOINT:
    boto3.DEFAULT_SESSION = LocalS3Session(endpoint_url=S3_ENDPOINT)
    manager_params.s3_bucket = local_s3_bucket(boto3.resource("s3"), name=S3_BUCKET)

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager(manager_params, browser_params, logger_kwargs=LOGGER_SETTINGS)

# At this point, Sentry should be initiated
if SENTRY_DSN:
    # Add crawler.py-specific context
    with sentry_sdk.configure_scope() as scope:
        # tags generate breakdown charts and search filters
        scope.set_tag("CRAWL_DIRECTORY", CRAWL_DIRECTORY)
        scope.set_tag("S3_BUCKET", S3_BUCKET)
        scope.set_tag("DISPLAY_MODE", DISPLAY_MODE)
        scope.set_tag("HTTP_INSTRUMENT", HTTP_INSTRUMENT)
        scope.set_tag("COOKIE_INSTRUMENT", COOKIE_INSTRUMENT)
        scope.set_tag("NAVIGATION_INSTRUMENT", NAVIGATION_INSTRUMENT)
        scope.set_tag("JS_INSTRUMENT", JS_INSTRUMENT)
        scope.set_tag("JS_INSTRUMENT_SETTINGS", JS_INSTRUMENT_SETTINGS)
        scope.set_tag("CALLSTACK_INSTRUMENT", CALLSTACK_INSTRUMENT)
        scope.set_tag("SAVE_CONTENT", SAVE_CONTENT)
        scope.set_tag("DWELL_TIME", DWELL_TIME)
        scope.set_tag("TIMEOUT", TIMEOUT)
        scope.set_tag("MAX_JOB_RETRIES", MAX_JOB_RETRIES)
        scope.set_tag("CRAWL_REFERENCE", "%s/%s" % (S3_BUCKET, CRAWL_DIRECTORY))
        # context adds addition information that may be of interest
        scope.set_context("PREFS", PREFS)
        scope.set_context(
            "crawl_config",
            {
                "REDIS_QUEUE_NAME": REDIS_QUEUE_NAME,
            },
        )
    # Send a sentry error message (temporarily - to easily be able
    # to compare error frequencies to crawl worker instance count)
    sentry_sdk.capture_message("Crawl worker started")

# Connect to job queue
job_queue = rediswq.RedisWQ(
    name=REDIS_QUEUE_NAME, host=REDIS_HOST, max_retries=MAX_JOB_RETRIES
)
manager.logger.info("Worker with sessionID: %s" % job_queue.sessionID())
manager.logger.info("Initial queue state: empty=%s" % job_queue.empty())

unsaved_jobs: List[bytes] = list()
unsaved_jobs_lock = Lock()

shutting_down = False


def on_shutdown(
    manager: TaskManager, unsaved_jobs_lock: Lock
) -> Callable[[signal.Signals, Any], None]:
    def actual_callback(s: signal.Signals, __: Any) -> None:
        global shutting_down
        manager.logger.error("Got interupted by %r, shutting down", s)
        with unsaved_jobs_lock:
            shutting_down = True
        manager.close(relaxed=False)
        sys.exit(1)

    return actual_callback


# Register signal listeners for shutdown
for sig in [signal.SIGTERM, signal.SIGINT]:
    signal.signal(sig, on_shutdown(manager, unsaved_jobs_lock))


def get_job_completion_callback(
    logger: logging.Logger,
    unsaved_jobs_lock: Lock,
    job_queue: rediswq.RedisWQ,
    job: bytes,
) -> Callable[[bool], None]:
    def callback(sucess: bool) -> None:
        with unsaved_jobs_lock:
            if sucess:
                logger.info("Job %r is done", job)
                job_queue.complete(job)
            else:
                logger.warning("Job %r got interrupted", job)
            unsaved_jobs.remove(job)

    return callback


no_job_since = None
# Crawl sites specified in job queue until empty
while not job_queue.empty():
    job_queue.check_expired_leases()
    with unsaved_jobs_lock:
        manager.logger.debug("Currently unfinished jobs are: %s", unsaved_jobs)
        for unsaved_job in unsaved_jobs:
            if not job_queue.renew_lease(unsaved_job, EXTENDED_LEASE_TIME):
                manager.logger.error("Unsaved job: %s timed out", unsaved_job)

    job = job_queue.lease(lease_secs=TIMEOUT + DWELL_TIME + 30, block=True, timeout=5)
    if job is None:
        manager.logger.info("Waiting for work")
        time.sleep(5)
        continue

    unsaved_jobs.append(job)
    retry_number = job_queue.get_retry_number(job)
    site_rank, site = job.decode("utf-8").split(",")
    if "://" not in site:
        site = "http://" + site
    manager.logger.info("Visiting %s..." % site)
    callback = get_job_completion_callback(
        manager.logger, unsaved_jobs_lock, job_queue, job
    )
    command_sequence = CommandSequence(
        site,
        blocking=True,
        reset=True,
        retry_number=retry_number,
        callback=callback,
        site_rank=site_rank,
    )
    command_sequence.get(sleep=DWELL_TIME, timeout=TIMEOUT)
    manager.execute_command_sequence(command_sequence)
else:
    manager.logger.info("Job queue finished, exiting.")
manager.close()

if SENTRY_DSN:
    sentry_sdk.capture_message("Crawl worker finished")
