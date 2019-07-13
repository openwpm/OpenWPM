from __future__ import absolute_import

import os
import time

from six.moves import range

from automation import CommandSequence, TaskManager
from automation.utilities import rediswq

import boto3
from test.utilities import LocalS3Session, local_s3_bucket

# Configuration via environment variables
NUM_BROWSERS = int(os.getenv('NUM_BROWSERS'))
REDIS_QUEUE_NAME = os.getenv('REDIS_QUEUE_NAME')
CRAWL_DIRECTORY = os.getenv('CRAWL_DIRECTORY')
S3_BUCKET = os.getenv('S3_BUCKET')
HTTP_INSTRUMENT = os.getenv('HTTP_INSTRUMENT')
COOKIE_INSTRUMENT = os.getenv('COOKIE_INSTRUMENT')
NAVIGATION_INSTRUMENT = os.getenv('NAVIGATION_INSTRUMENT')
JS_INSTRUMENT = os.getenv('JS_INSTRUMENT')
SAVE_JAVASCRIPT = os.getenv('SAVE_JAVASCRIPT')
DWELL_TIME = int(os.getenv('DWELL_TIME'))
TIMEOUT = int(os.getenv('TIMEOUT'))

# Loads the manager preference and NUM_BROWSERS copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Browser configuration
for i in range(NUM_BROWSERS):
    browser_params[i]['http_instrument'] = HTTP_INSTRUMENT == "1"
    browser_params[i]['cookie_instrument'] = COOKIE_INSTRUMENT == "1"
    browser_params[i]['navigation_instrument'] = NAVIGATION_INSTRUMENT == "1"
    browser_params[i]['js_instrument'] = JS_INSTRUMENT == "1"
    browser_params[i]['save_javascript'] = SAVE_JAVASCRIPT == "1"
    browser_params[i]['headless'] = True

# Manager configuration
manager_params['data_directory'] = '~/Desktop/%s/' % CRAWL_DIRECTORY
manager_params['log_directory'] = '~/Desktop/%s/' % CRAWL_DIRECTORY
manager_params['output_format'] = 's3'
manager_params['s3_bucket'] = S3_BUCKET
manager_params['s3_directory'] = CRAWL_DIRECTORY

# Allow the use of localstack's mock s3 service via an alternative s3 endpoint configuration
S3_ENDPOINT = os.getenv('S3_ENDPOINT')
if S3_ENDPOINT:
    boto3.DEFAULT_SESSION = LocalS3Session(endpoint_url=S3_ENDPOINT)
    manager_params['s3_bucket'] = local_s3_bucket(boto3.resource('s3'), name=S3_BUCKET)

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(manager_params, browser_params)

# Connect to job queue
job_queue = rediswq.RedisWQ(name=REDIS_QUEUE_NAME, host="redis")
print("Worker with sessionID: %s" % job_queue.sessionID())
print("Initial queue state: empty=%s" % job_queue.empty())

# Crawl sites specified in job queue until empty
while not job_queue.empty():
    job = job_queue.lease(lease_secs=120, block=True, timeout=5)
    if job is None:
        print("Waiting for work")
        time.sleep(1)
    else:
        site_rank, site = job.decode("utf-8").split(',')
        print("Visiting %s..." % site)
        command_sequence = CommandSequence.CommandSequence(
            site, reset=True
        )
        command_sequence.get(sleep=DWELL_TIME, timeout=TIMEOUT)
        manager.execute_command_sequence(command_sequence)
        job_queue.complete(job)

print("Job queue finished, exiting.")
manager.close()
