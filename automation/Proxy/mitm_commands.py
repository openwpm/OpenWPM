# This module parses MITM Proxy requests/reponses into (command, data pairs)
# This should mean that the MITMProxy code should simply pass the messages + its own data to this module
# TODO: deal with JavaScript

import datetime
from dateutil import parser

# msg is the message object given by MITM
# (crawl_id, url, method, referrer, top_url)
def process_general_mitm_request(db_socket, crawl_id, top_url, msg):
    if len(msg.headers['referer']) > 0:
        referrer = msg.headers['referer'][0]
    else:
        referrer = ''

    # log cookies if they exist
    if msg.get_cookies() is not None:
        process_cookies(db_socket, crawl_id, top_url, referrer, msg.get_cookies(), "request")

    data = (crawl_id, msg.get_url(), msg.method, referrer, str(msg.headers), top_url, str(datetime.datetime.now()))
    db_socket.send(("INSERT INTO http_requests (crawl_id, url, method, referrer, headers, top_url, time_stamp) VALUES (?,?,?,?,?,?,?)", data))


# msg is the message object given by MITM
# (crawl_id, url, method, referrer, response_status, response_status_text, top_url)
def process_general_mitm_response(db_socket, crawl_id, top_url, msg):
    if len(msg.request.headers['referer']) > 0:
        referrer = msg.request.headers['referer'][0]
    else:
        referrer = ''

    if len(msg.headers['location']) > 0:
        location = msg.headers['location'][0]
    else:
        location = ''

    # log cookies if they exist
    if msg.get_cookies() is not None:
        process_cookies(db_socket, crawl_id, top_url, referrer, msg.get_cookies(), "response")

    data = (crawl_id, msg.request.get_url(), msg.request.method, referrer, msg.code, msg.msg, str(msg.headers), location, top_url, str(datetime.datetime.now()))
    db_socket.send(("INSERT INTO http_responses (crawl_id, url, method, referrer, response_status, "
                      "response_status_text, headers, location, top_url, time_stamp) VALUES (?,?,?,?,?,?,?,?,?,?)", data))

# returns canonical date-time string
def parse_date(date):
    try:
        return str(parser.parse(date, fuzzy=True))
    except Exception as ex:
        return str(datetime.datetime.now())

# add an entry for a cookie to the table
def process_cookies(db_socket, crawl_id, top_url, referrer, cookies, http_type):
    for name in cookies:
        value, attr_dict = cookies[name]
        domain = '' if 'domain' not in attr_dict else unicode(attr_dict['domain'], errors='ignore')
        accessed = str(datetime.datetime.now())
        expiry = str(datetime.datetime.now()) if 'expires' not in attr_dict else parse_date(attr_dict['expires'])

        data = (crawl_id, domain, unicode(name, errors='ignore'), unicode(value, errors='ignore'),
                expiry, accessed, referrer, http_type, top_url)
        db_socket.send(("INSERT INTO cookies (crawl_id, domain, name, value, expiry, accessed, referrer, http_type, top_url) "
                      "VALUES (?,?,?,?,?,?,?,?,?)", data))
