# This module is used to extract persistent cookie IDs using the same heuristics from the PETS 2014 paper

import census_util
from collections import defaultdict
import sqlite3 as lite
from dateutil import parser

# builds a dictionary with keys = (domain, name) and values being list of cookie values
# values must be from non short-lived cookies and consistent across the crawls
# extracts from a single OpenWPM database
def extract_cookies_from_db(db_name):
    con = lite.connect(db_name)
    cur = con.cursor()

    # first, add all cookie/value pairs for cookies that live at least one month
    raw_cookie_dict = defaultdict(list)  # maps (domain, names) to lists of values
    for domain, name, value, access, expiry in cur.execute('SELECT domain, name, value, accessed, expiry FROM cookies'):
        domain = domain if len(domain) == 0 or domain[0] != "." else domain[1:]

        # prune away cookies with expiry times under a month
        if (parser.parse(expiry).replace(tzinfo=None) - parser.parse(access).replace(tzinfo=None)).days < 30:
            continue

        raw_cookie_dict[(domain, name)].append(value)

    # only keep cookies with values that remain constant throughout the crawl
    cookie_dict = {}
    for cookie in raw_cookie_dict:
        if census_util.all_same(raw_cookie_dict[cookie]):
            cookie_dict[cookie] = raw_cookie_dict[cookie][0]

    return cookie_dict

# takes in dictionaries of persistent, non-session cookies
# finds common ids that have values of the same length
# are not the same and have pairwise similarities < 0.9 (which covers all being equal)
# an ID must appear in at least 2 different crawls (otherwise, can't make a definitive statement about it)
# prunes away cookies with lengths less than or equal to 5 (these strings are probably too short
# returns dictionary with domains as keys and cookie names as values
def extract_persistent_ids(cookie_dicts):
    raw_id_dict = defaultdict(list)  # for each cookie, a list of the values across each crawl

    # combine all smaller cookie dictionaries into a larger dictionary
    for cookie_dict in cookie_dicts:
        for cookie in cookie_dict:
            raw_id_dict[cookie].append(cookie_dict[cookie])

    domain_dict = defaultdict(list)  # for each domain,list of candidate ID cookies

    # prune away cookies that fail one of our unique ID heuristics
    for cookie in raw_id_dict:
        if len(raw_id_dict[cookie]) <= 1 or len(raw_id_dict[cookie][0]) <= 5 \
                or not census_util.all_same_len(raw_id_dict[cookie]) \
                or not census_util.all_dissimilar(raw_id_dict[cookie]):
            continue

        domain_dict[cookie[0]].append(cookie[1])

    return domain_dict

if __name__ == "__main__":
    c1 =  extract_cookies_from_db("/home/christian/Desktop/crawl1.sqlite")
    c2 =  extract_cookies_from_db("/home/christian/Desktop/crawl2.sqlite")
    print extract_persistent_ids([c1, c2])
