# This module parses MITM Proxy requests/responses into (command, data pairs)
# This should mean that the MITMProxy code should simply pass the messages + its own data to this module

from urlparse import urlparse
import datetime
import mmh3
import json
import zlib
import os

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


def process_general_mitm_request(db_socket, browser_params, visit_id, msg):
    """ Logs a HTTP request object """
    referrer = msg.request.headers['referer'][0] if len(msg.request.headers['referer']) > 0 else ''

    data = (browser_params['crawl_id'],
            encode_to_unicode(msg.request.url),
            msg.request.method,
            encode_to_unicode(referrer),
            json.dumps(msg.request.headers.get_state()),
            visit_id,
            str(datetime.datetime.now()))

    db_socket.send(("INSERT INTO http_requests (crawl_id, url, method, referrer, headers, "
                    "visit_id, time_stamp) VALUES (?,?,?,?,?,?,?)", data))


def process_general_mitm_response(db_socket, ldb_socket, logger, browser_params, visit_id, msg):
    """ Logs a HTTP response object and, if necessary, """
    referrer = msg.request.headers['referer'][0] if len(msg.request.headers['referer']) > 0 else ''
    location = msg.response.headers['location'][0] if len(msg.response.headers['location']) > 0 else ''

    content_hash = save_javascript_content(ldb_socket, logger, browser_params, msg)

    data = (browser_params['crawl_id'],
            encode_to_unicode(msg.request.url),
            encode_to_unicode(msg.request.method),
            encode_to_unicode(referrer),
            msg.response.code,
            msg.response.msg,
            json.dumps(msg.response.headers.get_state()),
            encode_to_unicode(location),
            visit_id,
            str(datetime.datetime.now()),
            content_hash)

    db_socket.send(("INSERT INTO http_responses (crawl_id, url, method, referrer, response_status, "
                    "response_status_text, headers, location, visit_id, time_stamp, content_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?)", data))


def save_javascript_content(ldb_socket, logger, browser_params, msg):
    """ Save javascript files de-duplicated and compressed on disk """
    if not browser_params['save_javascript']:
        return

    # Check if this response is javascript content
    is_js = False
    if (len(msg.response.headers['Content-Type']) > 0 and
       'javascript' in msg.response.headers['Content-Type'][0]):
        is_js = True
    if not is_js and urlparse(msg.request.url).path.split('.')[-1] == 'js':
        is_js = True
    if not is_js:
        return

    # Decompress any content with compression
    # We want files to hash to the same value
    # Firefox currently only accepts gzip/deflate
    script = ''
    content_encoding = msg.response.headers['Content-Encoding']
    if (len(content_encoding) == 0 or
            content_encoding[0].lower() == 'utf-8' or
            content_encoding[0].lower() == 'identity' or
            content_encoding[0].lower() == 'none' or
            content_encoding[0].lower() == 'ansi_x3.4-1968' or
            content_encoding[0].lower() == 'utf8' or
            content_encoding[0] == ''):
        script = msg.response.content
    elif 'gzip' in content_encoding[0].lower():
        try:
            script = zlib.decompress(msg.response.content, zlib.MAX_WBITS|16)
        except zlib.error as e:
            logger.error('BROWSER %i: Received zlib error when trying to decompress gzipped javascript: %s' % (browser_params['crawl_id'],str(e)))
            return
    elif 'deflate' in content_encoding[0].lower():
        try:
            script = zlib.decompress(msg.response.content, -zlib.MAX_WBITS)
        except zlib.error as e:
            logger.error('BROWSER %i: Received zlib error when trying to decompress deflated javascript: %s' % (browser_params['crawl_id'],str(e)))
            return
    else:
        logger.error('BROWSER %i: Received Content-Encoding %s. Not supported by Firefox, skipping archive.' % (browser_params['crawl_id'], str(content_encoding)))
        return

    ldb_socket.send(script)

    # Hash script for deduplication on disk
    hasher = mmh3.hash128
    script_hash = str(hasher(script) >> 64)

    return script_hash
