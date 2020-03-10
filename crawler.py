
import json
import os
import time

import boto3
import sentry_sdk

from automation import CommandSequence, MPLogger, TaskManager
from automation.utilities import rediswq
from test.utilities import LocalS3Session, local_s3_bucket

# Configuration via environment variables
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-box')
REDIS_QUEUE_NAME = os.getenv('REDIS_QUEUE_NAME', 'crawl-queue')
CRAWL_DIRECTORY = os.getenv('CRAWL_DIRECTORY', 'crawl-data')
S3_BUCKET = os.getenv('S3_BUCKET', 'openwpm-crawls')
HTTP_INSTRUMENT = os.getenv('HTTP_INSTRUMENT', '1') == '1'
COOKIE_INSTRUMENT = os.getenv('COOKIE_INSTRUMENT', '1') == '1'
NAVIGATION_INSTRUMENT = os.getenv('NAVIGATION_INSTRUMENT', '1') == '1'
JS_INSTRUMENT = os.getenv('JS_INSTRUMENT', '1') == '1'
JS_INSTRUMENT_MODULES = os.getenv('JS_INSTRUMENT_MODULES', None)
SAVE_CONTENT = os.getenv('SAVE_CONTENT', '')
PREFS = os.getenv('PREFS', None)
DWELL_TIME = int(os.getenv('DWELL_TIME', '10'))
TIMEOUT = int(os.getenv('TIMEOUT', '60'))
SENTRY_DSN = os.getenv('SENTRY_DSN', None)
LOGGER_SETTINGS = MPLogger.parse_config_from_env()
MAX_JOB_RETRIES = int(os.getenv('MAX_JOB_RETRIES', '2'))

# Loads the default manager params
# We can't use more than one browser per instance because the job management
# code below requires blocking commands. For more context see:
# https://github.com/mozilla/OpenWPM/issues/470
NUM_BROWSERS = 1
manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Browser configuration
for i in range(NUM_BROWSERS):
    browser_params[i]['http_instrument'] = HTTP_INSTRUMENT
    browser_params[i]['cookie_instrument'] = COOKIE_INSTRUMENT
    browser_params[i]['navigation_instrument'] = NAVIGATION_INSTRUMENT
    browser_params[i]['js_instrument'] = JS_INSTRUMENT
    if JS_INSTRUMENT_MODULES:
        browser_params[i]['js_instrument_modules'] = JS_INSTRUMENT_MODULES
    if SAVE_CONTENT == '1':
        browser_params[i]['save_content'] = True
    elif SAVE_CONTENT == '0':
        browser_params[i]['save_content'] = False
    else:
        browser_params[i]['save_content'] = SAVE_CONTENT
    if PREFS:
        browser_params[i]['prefs'] = json.loads(PREFS)
    browser_params[i]['headless'] = True

# Manager configuration
manager_params['data_directory'] = '~/Desktop/%s/' % CRAWL_DIRECTORY
manager_params['log_directory'] = '~/Desktop/%s/' % CRAWL_DIRECTORY
manager_params['output_format'] = 's3'
manager_params['s3_bucket'] = S3_BUCKET
manager_params['s3_directory'] = CRAWL_DIRECTORY

# Allow the use of localstack's mock s3 service
S3_ENDPOINT = os.getenv('S3_ENDPOINT')
if S3_ENDPOINT:
    boto3.DEFAULT_SESSION = LocalS3Session(endpoint_url=S3_ENDPOINT)
    manager_params['s3_bucket'] = local_s3_bucket(
        boto3.resource('s3'), name=S3_BUCKET)

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(manager_params, browser_params,
                                  logger_kwargs=LOGGER_SETTINGS)

# At this point, Sentry should be initiated
if SENTRY_DSN:
    # Add crawler.py-specific context
    with sentry_sdk.configure_scope() as scope:
        # tags generate breakdown charts and search filters
        scope.set_tag('CRAWL_DIRECTORY', CRAWL_DIRECTORY)
        scope.set_tag('S3_BUCKET', S3_BUCKET)
        scope.set_tag('HTTP_INSTRUMENT', HTTP_INSTRUMENT)
        scope.set_tag('COOKIE_INSTRUMENT', COOKIE_INSTRUMENT)
        scope.set_tag('NAVIGATION_INSTRUMENT', NAVIGATION_INSTRUMENT)
        scope.set_tag('JS_INSTRUMENT', JS_INSTRUMENT)
        scope.set_tag('JS_INSTRUMENT_MODULES', JS_INSTRUMENT)
        scope.set_tag('SAVE_CONTENT', SAVE_CONTENT)
        scope.set_tag('DWELL_TIME', DWELL_TIME)
        scope.set_tag('TIMEOUT', TIMEOUT)
        scope.set_tag('MAX_JOB_RETRIES', MAX_JOB_RETRIES)
        scope.set_tag('CRAWL_REFERENCE', '%s/%s' %
                      (S3_BUCKET, CRAWL_DIRECTORY))
        # context adds addition information that may be of interest
        scope.set_context("PREFS", PREFS)
        scope.set_context("crawl_config", {
            'REDIS_QUEUE_NAME': REDIS_QUEUE_NAME,
        })
    # Send a sentry error message (temporarily - to easily be able
    # to compare error frequencies to crawl worker instance count)
    sentry_sdk.capture_message("Crawl worker started")

# Connect to job queue
job_queue = rediswq.RedisWQ(
    name=REDIS_QUEUE_NAME,
    host=REDIS_HOST,
    max_retries=MAX_JOB_RETRIES
)
manager.logger.info("Worker with sessionID: %s" % job_queue.sessionID())
manager.logger.info("Initial queue state: empty=%s" % job_queue.empty())

# Crawl sites specified in job queue until empty
while not job_queue.empty():
    job_queue.check_expired_leases()
    job = job_queue.lease(
        lease_secs=TIMEOUT + DWELL_TIME + 30, block=True, timeout=5
    )

    if job is None:
        manager.logger.info("Waiting for work")
        time.sleep(5)
        continue

    retry_number = job_queue.get_retry_number(job)
    site_rank, site = job.decode("utf-8").split(',')
    if "://" not in site:
        site = "http://" + site
    manager.logger.info("Visiting %s..." % site)
    command_sequence = CommandSequence.CommandSequence(
        site, blocking=True, reset=True, retry_number=retry_number,
        site_rank=site_rank
    )
    command_sequence.get(sleep=DWELL_TIME, timeout=TIMEOUT)
    manager.execute_command_sequence(command_sequence)
    job_queue.complete(job)

manager.logger.info("Job queue finished, exiting.")
manager.close()

if SENTRY_DSN:
    sentry_sdk.capture_message("Crawl worker finished")
