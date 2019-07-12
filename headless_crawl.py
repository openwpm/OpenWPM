from __future__ import absolute_import
import boto3
import random
import os

from six.moves import range

from automation import CommandSequence, TaskManager

from io import BytesIO

NUM_BROWSERS = int(os.getenv('NUM_BROWSERS'))
S3_BUCKET = os.getenv('S3_BUCKET')
S3_CRAWL_QUEUE = os.getenv('S3_CRAWL_QUEUE')
S3_DIRECTORY = os.getenv('S3_DIRECTORY')
S3_REGION = os.getenv('S3_REGION')
HTTP_INSTRUMENT = os.getenv('HTTP_INSTRUMENT')
COOKIE_INSTRUMENT = os.getenv('COOKIE_INSTRUMENT')
NAVIGATION_INSTRUMENT = os.getenv('NAVIGATION_INSTRUMENT')
JS_INSTRUMENT = os.getenv('JS_INSTRUMENT')
DWELL_TIME = int(os.getenv('DWELL_TIME'))
TIMEOUT = int(os.getenv('TIMEOUT'))

# Get lists of sites from files in S3
s3 = boto3.client('s3', region_name=S3_REGION)
bucket_name = S3_BUCKET

paginator = s3.get_paginator('list_objects_v2')
page_iterator = paginator.paginate(Bucket=bucket_name,
                                   Prefix=S3_CRAWL_QUEUE)

keys = []
for page in page_iterator:
    for content in page['Contents']:
        keys.append(content['Key'])

key = keys[random.randrange(len(keys))]
print key

obj = s3.get_object(Bucket=bucket_name, Key=key)

sites = []

for url in BytesIO(obj['Body'].read()):
    sites.append(url.strip())

s3.delete_object(Bucket=bucket_name, Key=key)

# Loads the manager preference and 3 copies of the default browser dictionaries
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

manager_params['output_format'] = 's3'
manager_params['s3_bucket'] = S3_BUCKET
manager_params['s3_directory'] = S3_DIRECTORY

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(manager_params, browser_params)

# Visits the sites with all browsers simultaneously
for site in sites:
    command_sequence = CommandSequence.CommandSequence(site, reset=True)
    command_sequence.get(sleep=DWELL_TIME, timeout=TIMEOUT)
    manager.execute_command_sequence(command_sequence, index='**')
# Shuts down the browsers and waits for the data to finish logging
manager.close()
