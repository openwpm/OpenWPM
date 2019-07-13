from __future__ import absolute_import

import os
import time

from six.moves import range

from .OpenWPM.automation import CommandSequence, TaskManager
from .OpenWPM.automation.utilities import rediswq

NUM_BROWSERS = 1
CRAWL_DIRECTORY = os.getenv('CRAWL_DIRECTORY')
JOB_QUEUE = os.getenv('REDIS_QUEUE_NAME')

manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Browser configuration
for i in range(NUM_BROWSERS):
    browser_params[i]['cookie_instrument'] = True
    browser_params[i]['js_instrument'] = True
    browser_params[i]['save_javascript'] = True
    browser_params[i]['http_instrument'] = True
    browser_params[i]['navigation_instrument'] = True
    browser_params[i]['headless'] = True

# Manager configuration
manager_params['data_directory'] = '~/Desktop/%s/' % CRAWL_DIRECTORY
manager_params['log_directory'] = '~/Desktop/%s/' % CRAWL_DIRECTORY
manager_params['output_format'] = 's3'
manager_params['s3_bucket'] = 'openwpm-crawls'
manager_params['s3_directory'] = CRAWL_DIRECTORY
manager = TaskManager.TaskManager(manager_params, browser_params)

# Connect to job queue
job_queue = rediswq.RedisWQ(name=JOB_QUEUE, host="redis")
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
            'http://' + site, reset=True
        )
        command_sequence.get(sleep=10, timeout=60)
        manager.execute_command_sequence(command_sequence)
        job_queue.complete(job)

print("Job queue finished, exiting.")
manager.close()
