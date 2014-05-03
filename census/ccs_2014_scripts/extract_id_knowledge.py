# THIS MODULE IS USED TO MEASURE THE EXTENT TO WHICH IDS ARE SPREAD

import sqlite3 as lite
import census_util
from collections import defaultdict

# MAPS IDS TO THE PARTIES THAT WE DEFINITELY KNOW HAVE THEM
# first, we can look at the list of cookie owners that know the id (seen in the dictionary)
# next, we can look at the http_responses and locations
# finally, we can look at the http_requests
def build_id_knowledge_dictionary(cookie_id_dict, cookie_db):
    id_knowledge_dict = defaultdict(list)

    # first, extract the cookies
    for cookie_id in cookie_id_dict:
        for cookie in cookie_id_dict[cookie_id]:
            id_knowledge_dict[cookie_id].append(census_util.extract_domain(cookie[0]))

    # connect to the cookie database
    conn = lite.connect(cookie_db)
    cur = conn.cursor()

    # scans through the urls/ referrers from http_requests
    # if the id is embedded in the url (or referrer) then we know the url (or referrer) tld knows the id
    # we also note that if id is in the referrer, the url knows it too (but not vice-versa)
    for url, referrer in cur.execute('SELECT DISTINCT url, referrer FROM http_requests'):
        short_url = census_util.extract_domain(url)
        short_referrer = census_util.extract_domain(referrer)

        for cookie_id in cookie_id_dict:
            if cookie_id in url:
                id_knowledge_dict[cookie_id].append(short_url)
            if cookie_id in referrer:
                id_knowledge_dict[cookie_id].append(short_referrer)
                id_knowledge_dict[cookie_id].append(short_url)

    # scans through the urls / referrers / locations from http_responses
    # if one of these strings contains an id, then we know that entity owns the id
    # if the referrer contains an id, then we know that the location and url know it as well
    # if the location contains an id, then we know that the url running the redirection knows it as well
    for url, referrer, location in cur.execute('SELECT DISTINCT url, referrer, location FROM http_responses'):
        short_url = census_util.extract_domain(url)
        short_referrer = census_util.extract_domain(referrer)
        short_location = census_util.extract_domain(location)

        for cookie_id in cookie_id_dict:
            if cookie_id in url:
                id_knowledge_dict[cookie_id].append(short_url)
            if cookie_id in location:
                id_knowledge_dict[cookie_id].append(short_location)
                id_knowledge_dict[cookie_id].append(short_url)
            if cookie_id in referrer:
                id_knowledge_dict[cookie_id].append(short_referrer)
                id_knowledge_dict[cookie_id].append(short_url)
                id_knowledge_dict[cookie_id].append(short_location)

    # remove duplicates and sort results before returning the final dictionary
    for cookie_id in id_knowledge_dict:
        unique_domains = census_util.unique(id_knowledge_dict[cookie_id])
        unique_domains.sort()
        if '' in unique_domains:
            unique_domains.remove('')
        id_knowledge_dict[cookie_id] = unique_domains

    return id_knowledge_dict


## MAPS DOMAINS TO THE LISTS OF IDS THAT THEY KNOW
# takes the dictionary produced by build_id_knowledge_dictionary and returns its inverse
# in particular, the keys of this dictionary is the domains and the values are lists of the ids known by the domain
def map_domains_to_known_ids(id_knowledge_dict):
    domain_knowledge_dict = defaultdict(list)

    # build up the domain -> id mapping
    for cookie_id in id_knowledge_dict:
        for domain in id_knowledge_dict[cookie_id]:
            domain_knowledge_dict[domain].append(cookie_id)

    # sort the results
    for domain in domain_knowledge_dict:
        id_list = domain_knowledge_dict[domain]
        id_list.sort()
        domain_knowledge_dict[domain] = id_list

    return domain_knowledge_dict
