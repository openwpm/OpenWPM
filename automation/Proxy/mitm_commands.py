# This module parses MITM Proxy requests/responses into (command, data pairs)
# This should mean that the MITMProxy code should simply pass the messages + its own data to this module

import datetime

def process_general_mitm_request(db_socket, crawl_id, top_url, msg):
    """ Logs a HTTP request object """
    referrer = msg.headers['referer'][0] if len(msg.headers['referer']) > 0 else ''

    data = (crawl_id, msg.get_url(), msg.method, referrer, str(msg.headers), top_url, str(datetime.datetime.now()))
    db_socket.send(("INSERT INTO http_requests (crawl_id, url, method, referrer, headers, "
                    "top_url, time_stamp) VALUES (?,?,?,?,?,?,?)", data))


def process_general_mitm_response(db_socket, crawl_id, top_url, msg):
    """ Logs a HTTP response object and, if necessary, """
    referrer = msg.headers['referer'][0] if len(msg.headers['referer']) > 0 else ''
    location = msg.headers['location'][0] if len(msg.headers['location']) > 0 else ''

    data = (crawl_id, msg.request.get_url(), msg.request.method, referrer, msg.code, msg.msg, str(msg.headers),
            location, top_url, str(datetime.datetime.now()))
    db_socket.send(("INSERT INTO http_responses (crawl_id, url, method, referrer, response_status, "
                    "response_status_text, headers, location, top_url, time_stamp) VALUES (?,?,?,?,?,?,?,?,?,?)", data))
