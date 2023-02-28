import json
from datetime import datetime
import sqlite3

from pandas import read_sql_query

# from .domain import get_ps_plus_1


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


if __name__ == '__main__':
    # pass
    sqliteConnection = sqlite3.connect('datadir/stateful/crawl-data-ublock.sqlite')
    cursor = sqliteConnection.cursor()
    # responses = get_responses_from_visits(sqliteConnection, [8869605158283901])
    # responses.to_csv('responses_ublock.csv', index=False)
    print(get_host_from_url('https://googleads.g.doubleclick.net/pagead/id?slf_rd=1'))


    # with open('responses.csv', 'r') as t1, open('responses_ublock.csv', 'r') as t2:
    #     fileone = t1.readlines()
    #     filetwo = t2.readlines()

    # with open('responses_diff.csv', 'w') as outFile:
    #     for line in filetwo:
    #         if line not in fileone:
    #             outFile.write(line)
    # print(type(responses))
    # print(get_set_of_script_hosts_from_call_stack("Aj@https://www.google.com/?gws_rd=ssl:113:405;nullIj@https://www.google.com/?gws_rd=ssl:113:618;nullnull@https://www.google.com/?gws_rd=ssl:113:825;nullnull@https://www.google.com/?gws_rd=ssl:113:920;nullnull@https://www.google.com/?gws_rd=ssl:115:3;null"))

