import os

import sentry_sdk


def activate_sentry(dsn, integrations=None):
    sentry_sdk.init(dsn, integrations)
    with sentry_sdk.configure_scope() as scope:
        NUM_BROWSERS = int(os.getenv('NUM_BROWSERS', '1'))
        REDIS_QUEUE_NAME = os.getenv('REDIS_QUEUE_NAME', 'crawl-queue')
        CRAWL_DIRECTORY = os.getenv('CRAWL_DIRECTORY', 'crawl-data')
        S3_BUCKET = os.getenv('S3_BUCKET', 'openwpm-crawls')
        HTTP_INSTRUMENT = os.getenv('HTTP_INSTRUMENT', '1') == '1'
        COOKIE_INSTRUMENT = os.getenv('COOKIE_INSTRUMENT', '1') == '1'
        NAVIGATION_INSTRUMENT = os.getenv('NAVIGATION_INSTRUMENT', '1') == '1'
        JS_INSTRUMENT = os.getenv('JS_INSTRUMENT', '1') == '1'
        SAVE_JAVASCRIPT = os.getenv('SAVE_JAVASCRIPT', '0') == '1'
        DWELL_TIME = int(os.getenv('DWELL_TIME', '10'))
        TIMEOUT = int(os.getenv('TIMEOUT', '60'))
        # tags generate breakdown charts and search filters
        scope.set_tag('NUM_BROWSERS', NUM_BROWSERS)
        scope.set_tag('CRAWL_DIRECTORY', CRAWL_DIRECTORY)
        scope.set_tag('S3_BUCKET', S3_BUCKET)
        scope.set_tag('HTTP_INSTRUMENT', HTTP_INSTRUMENT)
        scope.set_tag('COOKIE_INSTRUMENT', COOKIE_INSTRUMENT)
        scope.set_tag('NAVIGATION_INSTRUMENT', NAVIGATION_INSTRUMENT)
        scope.set_tag('JS_INSTRUMENT', JS_INSTRUMENT)
        scope.set_tag('SAVE_JAVASCRIPT', SAVE_JAVASCRIPT)
        scope.set_tag('DWELL_TIME', DWELL_TIME)
        scope.set_tag('TIMEOUT', TIMEOUT)
        scope.set_tag('CRAWL_REFERENCE', '%s/%s' %
                      (S3_BUCKET, CRAWL_DIRECTORY))
        # context adds addition information that may be of interest
        scope.set_context("crawl_config", {
            'REDIS_QUEUE_NAME': REDIS_QUEUE_NAME,
        })
