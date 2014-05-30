# This module parses MITM Proxy requests/responses into (command, data pairs)
# This should mean that the MITMProxy code should simply pass the messages + its own data to this module

import datetime
from dateutil import parser


def process_general_mitm_request(db_socket, crawl_id, top_url, msg):
    """ Logs a HTTP request object """
    referrer = msg.headers['referer'][0] if len(msg.headers['referer']) > 0 else ''

    # log cookies if they exist
    if msg.get_cookies() is not None:
        host = msg.headers['host'][0] if 'host' in msg.headers else ''
        process_cookies(db_socket, crawl_id, top_url, referrer, msg.get_cookies(), host, "request")

    data = (crawl_id, msg.get_url(), msg.method, referrer, str(msg.headers), top_url, str(datetime.datetime.now()))
    db_socket.send(("INSERT INTO http_requests (crawl_id, url, method, referrer, headers, "
                    "top_url, time_stamp) VALUES (?,?,?,?,?,?,?)", data))


def process_general_mitm_response(db_socket, crawl_id, top_url, msg):
    """ Logs a HTTP response object and, if necessary, """
    referrer = msg.headers['referer'][0] if len(msg.headers['referer']) > 0 else ''
    location = msg.headers['location'][0] if len(msg.headers['location']) > 0 else ''

    # log cookies if they exist
    if msg.get_cookies() is not None:
        process_cookies(db_socket, crawl_id, top_url, referrer, msg.get_cookies(), '', "response")

    data = (crawl_id, msg.request.get_url(), msg.request.method, referrer, msg.code, msg.msg, str(msg.headers),
            location, top_url, str(datetime.datetime.now()))
    db_socket.send(("INSERT INTO http_responses (crawl_id, url, method, referrer, response_status, "
                    "response_status_text, headers, location, top_url, time_stamp) VALUES (?,?,?,?,?,?,?,?,?,?)", data))


def parse_date(date):
    """ returns canonical date-time string for logging purposes """

    try:
        return str(parser.parse(date, fuzzy=True))
    except Exception:
        return str(datetime.datetime.now())


def process_cookies(db_socket, crawl_id, top_url, referrer, cookies, host, http_type):
    """ logs a list of HTTP cookies received by the proxy """

    for name in cookies:
        value, attr_dict = cookies[name]
        domain = '' if 'domain' not in attr_dict else unicode(attr_dict['domain'], errors='ignore')
        domain = host if http_type == "request" else domain
        accessed = str(datetime.datetime.now())
        expiry = str(datetime.datetime.now()) if 'expires' not in attr_dict else parse_date(attr_dict['expires'])

        data = (crawl_id, domain, unicode(name, errors='ignore'), unicode(value, errors='ignore'),
                expiry, accessed, referrer, http_type, top_url)
        db_socket.send(("INSERT INTO cookies (crawl_id, domain, name, value, expiry, accessed, referrer, "
                        "http_type, top_url) VALUES (?,?,?,?,?,?,?,?,?)", data))
