from build_cookie_table import build_http_cookie_table  

def run(db_path):
    """ Post-processing tasks to run after TaskManager finishes """
    print "Starting post-processing tasks..."
    
    build_http_cookie_table(db_path) # Parse HTTP Cookies
