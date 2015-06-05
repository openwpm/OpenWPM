# This module parses MITM Proxy requests/responses into (command, data pairs)
# This should mean that the MITMProxy code should simply pass the messages + its own data to this module

import datetime

def encode_to_unicode(msg):
    """ 
    Tries different encodings before setting on utf8 ignoring any errors 
    We can likely inspect the headers for an encoding as well, though it 
    won't always be correct.
    """
    try:
        msg = unicode(msg, 'utf8')
    except UnicodeDecodeError:
        try:
            msg = unicode(msg, 'ISO-8859-1')
        except UnicodeDecodeError:
            msg = unicode(msg, 'utf8', 'ignore')
    return msg


def process_general_mitm_request(db_socket, crawl_id, top_url, msg):
    """ Logs a HTTP request object """
    referrer = msg.request.headers['referer'][0] if len(msg.request.headers['referer']) > 0 else ''

    data = (crawl_id,
            encode_to_unicode(msg.request.url),
            msg.request.method,
            encode_to_unicode(referrer),
            encode_to_unicode(str(msg.request.headers)),
            top_url,
            str(datetime.datetime.now()))

    db_socket.send(("INSERT INTO http_requests (crawl_id, url, method, referrer, headers, "
                    "top_url, time_stamp) VALUES (?,?,?,?,?,?,?)", data))


def process_general_mitm_response(db_socket, crawl_id, top_url, msg):
    """ Logs a HTTP response object and, if necessary, """
    referrer = msg.request.headers['referer'][0] if len(msg.request.headers['referer']) > 0 else ''
    location = msg.response.headers['location'][0] if len(msg.response.headers['location']) > 0 else ''
    
    data = (crawl_id,
            encode_to_unicode(msg.request.url),
            encode_to_unicode(msg.request.method),
            encode_to_unicode(referrer),
            msg.response.code,
            msg.response.msg,
            encode_to_unicode(str(msg.response.headers)),
            encode_to_unicode(location),
            top_url,
            str(datetime.datetime.now()))
    
    db_socket.send(("INSERT INTO http_responses (crawl_id, url, method, referrer, response_status, "
                    "response_status_text, headers, location, top_url, time_stamp) VALUES (?,?,?,?,?,?,?,?,?,?)", data))
