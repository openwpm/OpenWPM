# This module is used to extract persistent cookie IDs using the same heuristics from the PETS 2014 paper

from collections import defaultdict
import difflib
import itertools
import sqlite3 as lite
from dateutil import parser
import datetime

# are all items the same?
def all_same(items):
    return all(x == items[0] for x in items)

# are all strings of the same length?
def all_same_len(items):
    return all(len(x) == len(items[0]) for x in items)

# Are two cookies more than 80% similar in accordance to Ratcliff-Obershelp metric
def ro_similar(seq1, seq2):
    return difflib.SequenceMatcher(a=seq1, b=seq2).ratio() > 0.8

# Are all cookies in a list pairwise-dissimilar (i.e. fail ro-test)
def all_dissimilar(items):
    pairs = list(itertools.combinations(items, 2))
    return all(not ro_similar(x[0], x[1]) for x in pairs)

# builds a dictionary with keys = (domain, name) and values being list of cookie values
# values must be from non short-lived cookies and consistent across the crawls
# after extracting from a _single_ FP database # TODO: our cookie database
def extract_cookies_from_db(db_name):
    con = lite.connect(db_name)
    cur = con.cursor()

    raw_cookie_dict = defaultdict(list) # cookie dict containing list of values
    for domain, name, value, access, expiry in cur.execute('SELECT domain, name, value, accessed, expiry FROM cookies'):
        # TODO: extract domains

        # prune away cookies with expiry times under a month
        if (parser.parse(expiry) - parser.parse(access)).days < 30:
            continue

        raw_cookie_dict[(domain, name)].append(value)

    # only keep cookies with values that remain constant throughout the crawl
    cookie_dict = {}
    for cookie in raw_cookie_dict:
        if all_same(raw_cookie_dict[cookie]):
            cookie_dict[cookie] = raw_cookie_dict[cookie][0]

    return cookie_dict

# takes in dictionaries of persistent, non-session cookies
# finds common ids that have values of the same length
# are not the same and have pairwise similarities < 0.9 (which covers all being equal)
# an ID must appear in at least 2 different crawls (otherwise, can't make a definitive statement about it)
def extract_persistent_ids(cookie_dicts):
    raw_id_dict = defaultdict(list)  # for each cookie, a list of the values across each crawl

    for cookie_dict in cookie_dicts:
        for cookie in cookie_dict:
            raw_id_dict[cookie].append(cookie_dict[cookie])

    for cookie in raw_id_dict:
        if len(raw_id_dict[cookie]) > 1 and all_same_len(raw_id_dict[cookie]) \
                and len(raw_id_dict[cookie][0]) > 5 and all_dissimilar(raw_id_dict[cookie]):
                pass
            #print str(cookie) + "\t" + str(raw_id_dict[cookie])

if __name__ == "__main__":
    c1 =  extract_cookies_from_db("/Users/Christian/Desktop/data/crawl1.sqlite")
    c2 =  extract_cookies_from_db("/Users/Christian/Desktop/data/crawl2.sqlite")
    c3 =  extract_cookies_from_db("/Users/Christian/Desktop/data/crawl3.sqlite")
    extract_persistent_ids([c1, c2, c3])