import difflib
import itertools
import urlparse
from tld import get_tld
from collections import defaultdict
import sqlite3 as lite

# are all items the same?
def all_same(items):
    return all(x == items[0] for x in items)

# are all strings of the same length?
def all_same_len(items):
    return all(len(x) == len(items[0]) for x in items)

# Are two cookies more than <sim> similar in accordance to Ratcliff-Obershelp metric
def ro_similar(seq1, seq2, sim=0.33):
    return difflib.SequenceMatcher(a=seq1, b=seq2).ratio() >= sim

# Are all cookies in a list pairwise-dissimilar (i.e. fail ro-test)
def all_dissimilar(items, sim=0.33):
    pairs = list(itertools.combinations(items, 2))
    return all(not ro_similar(x[0], x[1], sim) for x in pairs)

# gets the domain from a url
def extract_domain(url):
    url = url if url.startswith("http") else "http://" + url # hack since http utils require url to start with http
    try:
        return get_tld(url)
    except:
        return urlparse.urlparse(url).netloc

# returns the unique elements of an iterable
def unique(seq):
    # Not order preserving
    return {}.fromkeys(seq).keys()

# returns a defaultdict(list) such that all keys to the dict map to a list with > 1 value
def prune_list_dict(list_dict):
    pruned_dict = defaultdict(list)
    for key in list_dict:
        if len(list_dict[key]) > 1:
            pruned_dict[key] = list_dict[key]

    return pruned_dict

# sorts tuple of the form (x, count) in reverse order
def sort_tuples(tuple_list):
    return sorted(tuple_list, key = lambda  arr: arr[1], reverse=True)

# given a list of keys and a default dict of list, returns the union of dict[key] for all keys
def get_values_from_keys(keys, value_dict):
    values = set()
    for key in keys:
        values = values.union(set(value_dict[key]))

    return values

# builds a map of domains to the first parties on which they were seen
# uses HTTP requests to build up the content
def build_domain_map(wpm_db):
    domain_to_fp_map = defaultdict(list)

    conn = lite.connect(wpm_db)
    cur = conn.cursor()
    
    # builds a raw mapping of domains to first parties using requets
    for url, referrer, top_url in cur.execute('SELECT DISTINCT url, referrer, top_url FROM http_requests'):
        url = extract_domain(url)
        referrer = extract_domain(referrer)
        top_url = extract_domain(top_url)

        if referrer != '' and url != '' and referrer == top_url:
            domain_to_fp_map[url].append(top_url)
        
    # removes duplicates from the dictionary
    for domain in domain_to_fp_map:
        domain_to_fp_map[domain] = unique(domain_to_fp_map[domain])

    return domain_to_fp_map

