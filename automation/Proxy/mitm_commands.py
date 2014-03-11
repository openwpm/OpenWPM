# This module parses MITM Proxy requests/reponses into (command, data pairs)
# This should mean that the MITMProxy code should simply pass the messages + its own data to this module
# TODO: deal with JavaScript and Cookies

# msg is the message object given by MITM
# (crawl_id, url, method, referrer, top_url)
def process_general_mitm_request(db_queue, crawl_id, top_url, msg):
    if len(msg.headers['referer']) > 0:
        referrer = msg.headers['referer'][0]
    else:
        referrer = ''

    data = (crawl_id, msg.get_url(), msg.method, referrer, top_url)
    db_queue.put(("INSERT INTO http_requests (crawl_id, url, method, referrer, top_url) VALUES (?,?,?,?,?)", data))

# msg is the message object given by MITM
# (crawl_id, url, method, referrer, response_status, response_status_text, top_url)
def process_general_mitm_response(db_queue, crawl_id, top_url, msg):
    if len(msg.request.headers['referer']) > 0:
        referrer = msg.request.headers['referer'][0]
    else:
        referrer = ''

    data = (crawl_id, msg.request.get_url(), msg.request.method, referrer, msg.code, msg.msg, top_url)
    db_queue.put(("INSERT INTO http_responses (crawl_id, url, method, referrer, response_status, "
                   "response_status_text, top_url) VALUES (?,?,?,?,?,?,?)", data))
