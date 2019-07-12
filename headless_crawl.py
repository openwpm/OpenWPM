from __future__ import absolute_import
import os
from automation.utilities import rediswq

import boto3
from test.utilities import LocalS3Session, local_s3_bucket

from six.moves import range

from automation import CommandSequence, TaskManager

# Configuration via environment variables
NUM_BROWSERS = int(os.getenv('NUM_BROWSERS'))
REDIS_CRAWL_QUEUE = os.getenv('REDIS_CRAWL_QUEUE')
S3_BUCKET = os.getenv('S3_BUCKET')
S3_DIRECTORY = os.getenv('S3_DIRECTORY')
HTTP_INSTRUMENT = os.getenv('HTTP_INSTRUMENT')
COOKIE_INSTRUMENT = os.getenv('COOKIE_INSTRUMENT')
NAVIGATION_INSTRUMENT = os.getenv('NAVIGATION_INSTRUMENT')
JS_INSTRUMENT = os.getenv('JS_INSTRUMENT')
DWELL_TIME = int(os.getenv('DWELL_TIME'))
TIMEOUT = int(os.getenv('TIMEOUT'))

# Loads the manager preference and NUM_BROWSERS copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    browser_params[i]['http_instrument'] = HTTP_INSTRUMENT == "1"
    browser_params[i]['cookie_instrument'] = COOKIE_INSTRUMENT == "1"
    browser_params[i]['navigation_instrument'] = NAVIGATION_INSTRUMENT == "1"
    browser_params[i]['js_instrument'] = JS_INSTRUMENT == "1"
    browser_params[i]['headless'] = True

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '~/Desktop/'
manager_params['log_directory'] = '~/Desktop/'

# Use the S3Aggregator
manager_params['output_format'] = 's3'
manager_params['s3_bucket'] = S3_BUCKET
manager_params['s3_directory'] = S3_DIRECTORY

# Allow the use of localstack's mock s3 service if available
S3_ENDPOINT = os.getenv('S3_ENDPOINT')
if S3_ENDPOINT:
    boto3.DEFAULT_SESSION = LocalS3Session(endpoint_url=S3_ENDPOINT)
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    s3_bucket = local_s3_bucket(s3_resource, name=S3_BUCKET)

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(manager_params, browser_params)

# Get lists of sites from Redis
host="redis"
q = rediswq.RedisWQ(name=REDIS_CRAWL_QUEUE, host="redis")
print("Worker with sessionID: " +  q.sessionID())
print("Initial queue state: empty=" + str(q.empty()))

while not q.empty():
  item = q.lease(lease_secs=120, block=True, timeout=2)
  if item is not None:
    itemstr = item.decode("utf=8")
    print("Working on " + itemstr)
    site = itemstr

    # Visit the site with all browsers simultaneously
    command_sequence = CommandSequence.CommandSequence(site, reset=True)
    command_sequence.get(sleep=DWELL_TIME, timeout=TIMEOUT)
    manager.execute_command_sequence(command_sequence, index='**')

    q.complete(item)
  else:
    print("Waiting for work")
print("Queue empty, exiting")

# Shuts down the browsers and waits for the data to finish logging
manager.close()
