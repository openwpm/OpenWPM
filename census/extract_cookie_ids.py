# This module is used to extract persistent cookie IDs using the same heuristics from the PETS 2014 paper

import census_util
from collections import defaultdict
import sqlite3 as lite
from dateutil import parser

# builds a dictionary with keys = (domain, name) and values being list of cookie values
# values must be from non short-lived cookies and consistent across the crawls
# extracts from a single OpenWPM database
def extract_cookie_candidates_from_db(db_name):
    con = lite.connect(db_name)
    cur = con.cursor()

    # first, add all cookie/value pairs for cookies that live at least one month
    raw_cookie_dict = defaultdict(list)  # maps (domain, names) to lists of values
    for domain, name, value, access, expiry in cur.execute('SELECT domain, name, value, accessed, expiry FROM cookies'):
        domain = domain if len(domain) == 0 or domain[0] != "." else domain[1:]

        # prune away cookies with expiry times under a month
        if (parser.parse(expiry).replace(tzinfo=None) - parser.parse(access).replace(tzinfo=None)).days < 30:
            continue

        # add the basic values, then try to parse inner parameters and add them
        raw_cookie_dict[(domain, name)].append(value)
        add_inner_parameters(raw_cookie_dict, domain, name, value)

    # only keep cookies with values that remain constant throughout the crawl
    cookie_dict = {}
    for cookie in raw_cookie_dict:
        if census_util.all_same(raw_cookie_dict[cookie]):
            cookie_dict[cookie] = raw_cookie_dict[cookie][0]

    return cookie_dict

# goes through the cookies values and looks for values of the form id=XXX&time=YYYY
# then appends to raw_cookie_dict the cookie (domain, name#id) XXX
# and (domain, name#time) YYY
# currently uses two known delimiters
def add_inner_parameters(raw_cookie_dict, domain, name, value):
    delimiters = [":", "&"]  # currently known inner cookie delimiters
    for delimiter in delimiters:
        parts = value.split(delimiter)
        for part in parts:
            params = part.split("=")
            if len(params) == 2:
                raw_cookie_dict[(domain, name + "#" + params[0])].append(params[1])

# takes in dictionaries of persistent, non-session cookies
# finds common ids that have values of the same length
# are not the same and have pairwise similarities < 0.9 (which covers all being equal)
# an ID must appear in at least 2 different crawls (otherwise, can't make a definitive statement about it)
# prunes away cookies with lengths less than or equal to 5 (these strings are probably too short
# returns dictionary with domains as keys and cookie names as values
def extract_common_persistent_ids(cookie_dicts):
    raw_id_dict = defaultdict(list)  # for each cookie, a list of the values across each crawl

    # combine all smaller cookie dictionaries into a larger dictionary
    for cookie_dict in cookie_dicts:
        for cookie in cookie_dict:
            raw_id_dict[cookie].append(cookie_dict[cookie])

    domain_dict = defaultdict(list)  # for each domain,list of candidate ID cookies

    # prune away cookies that fail one of our unique ID heuristics
    for cookie in raw_id_dict:
        if len(raw_id_dict[cookie]) <= 1 or len(raw_id_dict[cookie][0]) <= 5 or len(raw_id_dict[cookie][0]) > 100 \
                or not census_util.all_same_len(raw_id_dict[cookie]) \
                or not census_util.all_dissimilar(raw_id_dict[cookie]):
            continue

        domain_dict[cookie[0]].append(cookie[1])

    return domain_dict

# given a dictionary of persistent ids, goes through a database
# and returns a dictionary with the persistent ids and their unique values
# in the database (for those that actually appear)
def extract_known_cookies_from_db(db_name, cookie_dict):
    con = lite.connect(db_name)
    cur = con.cursor()

    found_cookies = {}
    for domain, name, value in cur.execute('SELECT domain, name, value FROM cookies'):
        domain = domain if len(domain) == 0 or domain[0] != "." else domain[1:]

        # first search for most basic cookies
        if domain in cookie_dict and name in cookie_dict[domain]:
            found_cookies[(domain, name)] = value

            # next, look for potential nested cookies
            if "=" in value:
                for delimiter in ["&", ":"]:
                    parts = value.split(delimiter)
                    for part in parts:
                        params = part.split("=")
                        if len(params) == 2 and name + "#" + params[0] in cookie_dict[domain]:
                            found_cookies[(domain, name + "#" + params[0])] = params[1]

    return found_cookies

if __name__ == "__main__":
    c1 = extract_cookie_candidates_from_db("/home/christian/Desktop/crawl1.sqlite")
    c2 = extract_cookie_candidates_from_db("/home/christian/Desktop/crawl2.sqlite")
    extracted = extract_common_persistent_ids([c1, c2])
    known = extract_known_cookies_from_db("/home/christian/Desktop/crawl1.sqlite", extracted)