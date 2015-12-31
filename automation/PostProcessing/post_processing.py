import os

from build_cookie_table import build_http_cookie_table

def run(manager_params):
    """ Post-processing tasks to run after TaskManager finishes """
    print "Starting post-processing tasks..."

    db_path = manager_params['database_name']
    build_http_cookie_table(db_path) # Parse HTTP Cookies
