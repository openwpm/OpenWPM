##############################
#MAKE SURE TO RUN THIS FILE WITH SUDO  :) 
##############################


import json
from datetime import datetime
import sqlite3
from pandas import read_sql_query

from domain_utils import get_ps_plus_1


def get_set_of_script_hosts_from_call_stack(call_stack):
    """Return the urls of the scripts involved in the call stack."""
    script_urls = set()
    if not call_stack:
        return ""
    stack_frames = call_stack.strip().split("\n")
    for stack_frame in stack_frames:
        script_url = stack_frame.rsplit(":", 2)[0].\
            split("@")[-1].split(" line")[0]
        script_urls.add(get_host_from_url(script_url))
    return ", ".join(script_urls)


def get_host_from_url(url):
    return strip_scheme_www_and_query(url).split("/", 1)[0]


def strip_scheme_www_and_query(url):
    """Remove the scheme and query section of a URL."""
    if url:
        return url.split("//")[-1].split("?")[0].lstrip("www.")
    else:
        return ""


def get_initiator_from_call_stack(call_stack):
    """Return the bottom element of the call stack."""
    if call_stack and type(call_stack) == str:
        return call_stack.strip().split("\n")[-1]
    else:
        return ""


def get_initiator_from_req_call_stack(req_call_stack):
    """Return the bottom element of a request call stack.
    Request call stacks have an extra field (async_cause) at the end.
    """
    return get_initiator_from_call_stack(req_call_stack).split(";")[0]


def get_func_and_script_url_from_initiator(initiator):
    """Remove line number and column number from the initiator."""
    if initiator:
        return initiator.rsplit(":", 2)[0].split(" line")[0]
    else:
        return ""


def get_script_url_from_initiator(initiator):
    """Remove the scheme and query section of a URL."""
    if initiator:
        return initiator.rsplit(":", 2)[0].split("@")[-1].split(" line")[0]
    else:
        return ""


def get_set_of_script_urls_from_call_stack(call_stack):
    """Return the urls of the scripts involved in the call stack as a
    string."""
    if not call_stack:
        return ""
    return ", ".join(get_script_urls_from_call_stack_as_set(call_stack))


def get_script_urls_from_call_stack_as_set(call_stack):
    """Return the urls of the scripts involved in the call stack as a set."""
    script_urls = set()
    if not call_stack:
        return script_urls
    stack_frames = call_stack.strip().split("\n")
    for stack_frame in stack_frames:
        script_url = stack_frame.rsplit(":", 2)[0].\
            split("@")[-1].split(" line")[0]
        script_urls.add(script_url)
    return script_urls


def add_col_bare_script_url(js_df):
    """Add a col for script URL without scheme, www and query."""
    js_df['bare_script_url'] =\
        js_df['script_url'].map(strip_scheme_www_and_query)


def add_col_set_of_script_urls_from_call_stack(js_df):
    js_df['stack_scripts'] =\
        js_df['call_stack'].map(get_set_of_script_urls_from_call_stack)


def add_col_unix_timestamp(df):
    df['unix_time_stamp'] = df['time_stamp'].map(datetime_from_iso)


def datetime_from_iso(iso_date):
    """Convert from ISO."""
    iso_date = iso_date.rstrip("Z")
    # due to a bug we stored timestamps
    # without a leading zero, which can
    # be interpreted differently
    # .21Z should be .021Z
    # dateutils parse .21Z as .210Z

    # add the missing leading zero
    if iso_date[-3] == ".":
        rest, ms = iso_date.split(".")
        iso_date = rest + ".0" + ms
    elif iso_date[-2] == ".":
        rest, ms = iso_date.split(".")
        iso_date = rest + ".00" + ms

    try:
        # print(iso_date)
        return datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        # print "ISO", iso_date,
        # datetime.strptime(iso_date.rstrip("+0000"), "%Y-%m-%dT%H:%M:%S")
        return datetime.strptime(iso_date.rstrip("+0000"), "%Y-%m-%dT%H:%M:%S")


def get_cookie(headers):
    # not tested
    for item in headers:
        if item[0] == "Cookie":
            return item[1]
    return ""


def get_set_cookie(header):
    # not tested
    for item in json.loads(header):
        if item[0] == "Set-Cookie":
            return item[1]
    return ""


def get_responses_from_visits(con, visit_ids):
    visit_ids_str = "(%s)" % ",".join(str(x) for x in visit_ids)
    # qry = """SELECT r.id, r.crawl_id, r.visit_id, r.url,
    #             sv.site_url, sv.first_party, sv.site_rank,
    #             r.method, r.referrer, r.headers, r.response_status, r.location,
    #             r.time_stamp FROM http_responses as r
    #         LEFT JOIN site_visits as sv
    #         ON r.visit_id = sv.visit_id
    #         WHERE r.visit_id in %s;""" % visit_ids_str

    qry = """SELECT r.id, r.incognito, r.browser_id, r.visit_id,
                r.extension_session_uuid, r.event_ordinal, r.window_id,
                r.tab_id, r.frame_id, r.url, r.method, r.response_status,
                r.response_status_text, r.is_cached, r.headers, r.request_id,
                r.location, r.time_stamp, r.content_hash FROM http_responses as r
            LEFT JOIN site_visits as sv
            ON r.visit_id = sv.visit_id
            WHERE r.visit_id in %s;""" % visit_ids_str

    return read_sql_query(qry, con)


def get_requests_from_visits(con, visit_ids):
    visit_ids_str = "(%s)" % ",".join(str(x) for x in visit_ids)
    qry = """SELECT r.id, r.crawl_id, r.visit_id, r.url, r.top_level_url,
            sv.site_url, sv.first_party, sv.site_rank,
            r.method, r.referrer, r.headers, r.loading_href, r.req_call_stack,
            r.content_policy_type, r.post_body, r.time_stamp
            FROM http_requests as r
            LEFT JOIN site_visits as sv
            ON r.visit_id = sv.visit_id
            WHERE r.visit_id in %s;""" % visit_ids_str

    return read_sql_query(qry, con)


def get_set_of_script_ps1s_from_call_stack(script_urls):
    if len(script_urls):
        return ", ".join(
            set((get_ps_plus_1(x) or "") for x in script_urls.split(", ")))
    else:
        return ""


def add_col_set_of_script_ps1s_from_call_stack(js_df):
    js_df['stack_script_ps1s'] =\
        js_df['stack_scripts'].map(get_set_of_script_ps1s_from_call_stack)
    

def get_third_parties(con, visit_ids):
    visit_ids_str = "(%s)" % ",".join(str(x) for x in visit_ids)

    qry = """SELECT r.id, r.incognito, r.browser_id, r.visit_id,
                r.extension_session_uuid, r.event_ordinal, r.window_id,
                r.tab_id, r.frame_id, r.url, r.top_level_url,
                sv.site_url, sv.site_rank
                FROM http_requests as r
            LEFT JOIN site_visits as sv
            ON r.visit_id = sv.visit_id
            WHERE r.visit_id in %s;""" % visit_ids_str

    return read_sql_query(qry, con)
    
def get_fingerprinting(con, visit_ids):
    visit_ids_str = "(%s)" % ",".join(str(x) for x in visit_ids)

    qry = """SELECT r.id, r.incognito, r.browser_id, r.visit_id,
                r.extension_session_uuid, r.event_ordinal, r.page_scoped_event_ordinal, r.window_id,
                r.tab_id, r.frame_id, r.script_url, r.script_line, r.script_col,
                r.func_name, r.script_loc_eval, r.document_url, r.top_level_url,
                r.call_stack, r.symbol, r.operation, r.value, r.arguments, r.time_stamp, sv.site_url, sv.site_rank
                FROM javascript as r
            LEFT JOIN site_visits as sv
            ON r.visit_id = sv.visit_id
            WHERE r.visit_id in %s;""" % visit_ids_str

    return read_sql_query(qry, con)

def create_third_party_helper(first_url, second_url):
    first_word = first_url.split(".")[0]
    second_word = second_url.split(".")[0]
    return first_word in second_word or second_word in first_word

def create_third_party_json(third_party_df):
    third_party_collection = {}
    for index, row in third_party_df.iterrows():
        third_party_url = get_host_from_url(row['url'])
        first_party_url = get_host_from_url(row['site_url'])
        third_party_url_plus_1 = get_ps_plus_1(third_party_url)
        first_party_url_plus_1 = get_ps_plus_1(first_party_url)
        if first_party_url not in third_party_collection:
            third_parties = {}
            third_party_collection[first_party_url] = third_parties
            if third_party_url != first_party_url and third_party_url_plus_1 != first_party_url_plus_1 and \
                not create_third_party_helper(first_party_url,third_party_url):
                third_parties[third_party_url] = 1
        else:
            third_parties = third_party_collection[first_party_url]
            if third_party_url == first_party_url or third_party_url_plus_1 == first_party_url_plus_1 or \
                create_third_party_helper(first_party_url,third_party_url):
                continue
            elif third_party_url not in third_parties:
                third_parties[third_party_url] = 1
            else:
                third_parties[third_party_url] += 1
    
    return sum_third_parties(third_party_collection)


def sum_third_parties(third_party_collection):
    third_party_collection_copy = third_party_collection.copy()
    for first_party_url in third_party_collection_copy:
        third_parties_copy= third_party_collection_copy[first_party_url].copy()
        total_number_of_third_parties = 0
        for third_party_url in third_parties_copy:
            total_number_of_third_parties += third_parties_copy[third_party_url]
        third_party_collection[first_party_url]["TotalThirdParties"] = total_number_of_third_parties
    
    third_party_collection = sorted(third_party_collection.items(), key=lambda x: x[1]["TotalThirdParties"], reverse=True)
    return write_to_json_third_parties(third_party_collection)

def create_fingerprint_json(fingerprint_df, fingerprint_type):
    if fingerprint_type == "canvas":
        identifier = set(["CanvasRenderingContext2D", "HTMLCanvasElement"])
    elif fingerprint_type == "webRTC":
        identifier = set(["RTCPeerConnection"])
    elif fingerprint_type == "font":
        identifier = set(["CanvasRenderingContext2D.font"])
    else:
        raise Exception("Pick either 'canvas', 'webRTC', or 'font' for fingerprint_type")
    
    outter_dict = {}
    for index, row in fingerprint_df.iterrows():
        script_url = get_host_from_url(row['script_url'])
        if fingerprint_type == "font":
            split_identifier =  row['symbol']
        else:
            split_identifier = row['symbol'].split('.')[0]
        if row['site_url'] not in outter_dict:
            middle_dict = {}
            outter_dict[row['site_url']] = middle_dict
            inner_dict = {}
            middle_dict[script_url] = inner_dict
            if split_identifier in identifier:
                inner_dict[row['symbol']] = 1
        else:
            middle_dict = outter_dict[row['site_url']]
            if script_url not in middle_dict:
                inner_dict = {}
                middle_dict[script_url] = inner_dict
            else:
                inner_dict = middle_dict[script_url]
                if split_identifier in identifier:
                    if row['symbol'] not in inner_dict:
                        inner_dict[row['symbol']] = 1
                    else:
                        inner_dict[row['symbol']] += 1
    
    return remove_empty_dicts(outter_dict, fingerprint_type)


def remove_empty_dicts(outter_dict, fingerprint_type):
    outter_dict_copy = outter_dict.copy()
    for host_url_key in outter_dict_copy:
        middle_dict_copy = outter_dict_copy[host_url_key].copy()
        for script_url_key in middle_dict_copy:
            if len(middle_dict_copy[script_url_key]) == 0:
                del outter_dict[host_url_key][script_url_key]

    outter_dict_copy = outter_dict.copy()
    for host_url_key in outter_dict_copy:
        if (len(outter_dict_copy[host_url_key])) == 0:
            del outter_dict[host_url_key]

    return sum_fingerprint(outter_dict, fingerprint_type)


def sum_fingerprint(outter_dict, fingerprint_type):
    if fingerprint_type == 'canvas':
        identifier = 'CanvasTotal'
    elif fingerprint_type == 'webRTC':
        identifier = 'RTCPeerConnectionTotal'
    elif fingerprint_type == "font":
        identifier = 'FontTotal'

    outter_dict_copy = outter_dict.copy()
    for host_url_key in outter_dict_copy:
        middle_dict_copy = outter_dict_copy[host_url_key].copy()
        for script_url_key in middle_dict_copy:
            inner_dict_copy = middle_dict_copy[script_url_key].copy()
            total_fingerprint = 0
            for canvasElement in inner_dict_copy:
                total_fingerprint += inner_dict_copy[canvasElement]
            outter_dict[host_url_key][script_url_key][identifier] = total_fingerprint

    outter_dict_copy = outter_dict.copy()
    for host_url_key in outter_dict_copy:
        outter_dict[host_url_key] = sorted(outter_dict[host_url_key].items(), key=lambda x: x[1][identifier], reverse=True)

    # third_party_collection = sorted(third_party_collection.items(), key=lambda x: x[1]["TotalThirdParties"], reverse=True)
    return write_to_json_fingerprinting(outter_dict, fingerprint_type)

def write_to_json_fingerprinting(outter_dict, fingerprint_type):
    with open("fingerprinting_analysis_" + fingerprint_type + ".json", "w") as write_file:
        json.dump(outter_dict, write_file, indent=4)

def write_to_json_third_parties(third_party_collection):
    with open("third_parties.json", "w") as write_file:
        json.dump(third_party_collection, write_file, indent=4)

if __name__ == '__main__':
    # Connect to DB
    sqliteConnection = sqlite3.connect('datadir/stateful/crawl-data-vanilla.sqlite')
    cursor = sqliteConnection.cursor()
    
    #Grab visit ids for each website from fingerprinting table
    ids = [id[0] for id in cursor.execute("SELECT visit_id FROM javascript")]
    ids = list(set(ids))

    #Conduct fingerprinting analysis 
    fingerprint_df = get_fingerprinting(sqliteConnection, ids)
    create_fingerprint_json(fingerprint_df, "canvas")
    create_fingerprint_json(fingerprint_df, "webRTC")
    create_fingerprint_json(fingerprint_df, "font")

    #Grab ids from http_requests table
    ids = [id[0] for id in cursor.execute("SELECT visit_id FROM http_requests")]
    ids = list(set(ids))

    #Conduct third party URL analyses
    third_party_df = get_third_parties(sqliteConnection, ids)
    create_third_party_json(third_party_df)


    # print(get_ps_plus_1("vs.aws.haha.amazon.com"))
    # print(get_host_from_url("vs.aws.haha.amazon.com/hello/hi"))
    # print(create_third_party_helper("azure.com", "azure.microsoft.com"))