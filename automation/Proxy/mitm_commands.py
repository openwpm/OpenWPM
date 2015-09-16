# This module parses MITM Proxy requests/responses into (command, data pairs)
# This should mean that the MITMProxy code should simply pass the messages + its own data to this module

from urlparse import urlparse
import datetime
import pyhash
import zlib
import gzip
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


def process_general_mitm_request(db_socket, browser_params, manager_params, top_url, msg):
    """ Logs a HTTP request object """
    referrer = msg.request.headers['referer'][0] if len(msg.request.headers['referer']) > 0 else ''

    data = (browser_params['crawl_id'],
            encode_to_unicode(msg.request.url),
            msg.request.method,
            encode_to_unicode(referrer),
            encode_to_unicode(str(msg.request.headers)),
            top_url,
            str(datetime.datetime.now()))

    db_socket.send(("INSERT INTO http_requests (crawl_id, url, method, referrer, headers, "
                    "top_url, time_stamp) VALUES (?,?,?,?,?,?,?)", data))


def process_general_mitm_response(db_socket, logger, browser_params, manager_params, top_url, msg):
    """ Logs a HTTP response object and, if necessary, """
    referrer = msg.request.headers['referer'][0] if len(msg.request.headers['referer']) > 0 else ''
    location = msg.response.headers['location'][0] if len(msg.response.headers['location']) > 0 else ''
    
    content_hash = save_javascript_content(logger, browser_params, manager_params, msg)
    
    data = (browser_params['crawl_id'],
            encode_to_unicode(msg.request.url),
            encode_to_unicode(msg.request.method),
            encode_to_unicode(referrer),
            msg.response.code,
            msg.response.msg,
            encode_to_unicode(str(msg.response.headers)),
            encode_to_unicode(location),
            top_url,
            str(datetime.datetime.now()),
            content_hash)
    
    db_socket.send(("INSERT INTO http_responses (crawl_id, url, method, referrer, response_status, "
                    "response_status_text, headers, location, top_url, time_stamp, content_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?)", data))

 
def save_javascript_content(logger, browser_params, manager_params, msg):
    """ Save javascript files de-duplicated and compressed on disk """
    if not browser_params['save_javascript']:
        return

    # Check if this response is javascript content
    content_type = msg.response.headers['Content-Type']
    url_path = urlparse(msg.request.url).path 
    if (content_type != 'application/javascript' and
        content_type != 'application/x-javascript' and
        content_type != 'text/javascript' and
        url_path.split('.')[-1] != 'js'):
           return

    # Decompress any content with compression
    # We want files to hash to the same value
    # Firefox currently only accepts gzip/deflate
    script = ''
    if 'gzip' in msg.response.headers['Content-Encoding']:
        try:
            script = zlib.decompress(msg.response.content, zlib.MAX_WBITS|16)
        except zlib.error as e:
            logger.error('Received zlib error when trying to decompress gzipped javascript: %s' % str(e))
            return
    elif 'deflate' in msg.response.headers['Content-Encoding']:
        try:
            script = zlib.decompress(msg.response.content, -zlib.MAX_WBITS)
        except zlib.error as e:
            logger.error('Received zlib error when trying to decompress deflated javascript: %s' % str(e))
            return
    elif msg.response.headers['Content-Encoding'] == []:
        script = msg.response.content
    else:
        logger.error('Received Content-Encoding %s. Not supported by Firefox, skipping archive.' % str(msg.response.headers['Content-Encoding']))
        return
    path = os.path.join(manager_params['data_directory'],'javascript_files/')

    # Hash script for deduplication on disk
    hasher = pyhash.murmur3_x64_128()
    script_hash = str(hasher(script) >> 64)
    if os.path.isfile(path + script_hash + '.gz'):
        return script_hash

    if not os.path.exists(path):
        os.mkdir(path)
    with gzip.open(path + script_hash + '.gz', 'wb') as f:
        f.write(script)

    return script_hash
