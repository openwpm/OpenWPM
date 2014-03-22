import sqlite3 as lite
import urlparse
import census_util
from collections import defaultdict

def add_params(raw_params, domain, domain_dict):
    # add the entry assuming it does not exist
    if domain not in raw_params:
        raw_params[domain] = defaultdict(list)

    for param in domain_dict:
        for value in domain_dict[param]:
            raw_params[domain][param].append(value)

    return raw_params


def extract_parameters_from_db(db_name):
    raw_param_dict = {}

    con = lite.connect(db_name)
    cur = con.cursor()
    #raw_cookie_dict = defaultdict(list) # cookie dict containing list of values
    for url, in cur.execute('SELECT url FROM http_requests'):
        domain = census_util.extract_domain(url)
        query = urlparse.urlparse(url).query
        if query is None:
            continue

        param_dict = urlparse.parse_qs(query)
        if len(param_dict) == 0:
            continue

        raw_param_dict = add_params(raw_param_dict, domain, param_dict)

    # throw away parameters that do no stay the same the entire time
    param_dict = {}
    for domain in raw_param_dict:
        param_dict[domain] = {}
        for param in raw_param_dict[domain]:
            if census_util.all_same(raw_param_dict[domain][param]):
                param_dict[domain][param] = raw_param_dict[domain][param][0]

    return param_dict

def extract_persistent_parameters(param_dicts):
    raw_param_dict = {}
    for dict in param_dicts:
        for domain in dict:
            if domain not in raw_param_dict:
                raw_param_dict[domain] = defaultdict(list)

            for param in dict[domain]:
                raw_param_dict[domain][param].append(dict[domain][param])

    # extract same-lengthed parameter values that are also sufficiently dis-similar and long enough
    param_dict = {}
    for domain in raw_param_dict:
        param_dict[domain] = {}
        for param in raw_param_dict[domain]:
            if len(raw_param_dict[domain][param]) > 1 and len(raw_param_dict[domain][param][0]) > 5 \
                    and census_util.all_same_len(raw_param_dict[domain][param]) \
                    and census_util.all_dissimilar(raw_param_dict[domain][param]):
                print domain + "\t" + param + "\t" + str(raw_param_dict[domain][param])

if __name__ == "__main__":
    d1 = extract_parameters_from_db("/home/christian/Desktop/crawl1.sqlite")
    d2 = extract_parameters_from_db("/home/christian/Desktop/crawl2.sqlite")
    extract_persistent_parameters([d1, d2])