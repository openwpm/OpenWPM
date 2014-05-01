import networkx as nx
import extract_cookie_ids
import sqlite3 as lite
import census_util
import sigma_graph_json
from sets import Set
from collections import defaultdict
import itertools
import matplotlib.pyplot as plt
import random

# builds and returns a cookie synchronization graph
# nodes are websites and (directed) edges illustrate cookie values flowing between sites
# each node and edge contains the cookies that are available to them
# only includes cookies in the graph that are present in at least 1 transfer
def unique(seq):
    # Not order preserving
    return {}.fromkeys(seq).keys()

def cluster_domains_by_ids(known_cookies, http_db = None):
    cookie_dict = defaultdict(list)

    # cluster top level domains by if they own cookies that share the same id
    for cookie in known_cookies:
        domain = cookie[0].strip()
        if domain == '':
            continue

        domain = domain if domain.startswith("http") else "http://" + domain # hack since http utils require url to start with
        domain = census_util.extract_domain(domain)

        cookie_dict[known_cookies[cookie]].append(domain)

    if http_db is not None:
        con = lite.connect(http_db)
        cur = con.cursor()
        for url, referrer in cur.execute('SELECT DISTINCT url, referrer FROM http_requests'):
            short_url = census_util.extract_domain(url)
            
            for cookie in cookie_dict:
                if cookie in url:
                    cookie_dict[cookie].append(short_url)

    # delete duplicates
    for id_cookie in cookie_dict:
        cookie_dict[id_cookie] = unique(cookie_dict[id_cookie])
        
    
    return cookie_dict

# bare bones graph for now, will modify to be forward compatible
def build_graph_from_id_clusters(id_dict):
    G = nx.Graph()

    for cookie_id in id_dict:
        edge_list = list(itertools.combinations(id_dict[cookie_id], 2))
        
        for edge in edge_list:
            G.add_edge(edge[0], edge[1])

    node_dict = {}
    i = 0
    for node in G.nodes():
        node_dict[node] = i
        i += 1

    colors = [0] * len(G.nodes())

    for cookie_id in id_dict:
        color = random.random()
        for site in id_dict[cookie_id]:
            if site in node_dict:
                colors[node_dict[site]] = color

    return G, colors

if __name__ == "__main__":
    c1 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/crawl1.sqlite")
    c2 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/crawl2.sqlite")
    extracted = extract_cookie_ids.extract_common_persistent_ids([c1, c2])
    known = extract_cookie_ids.extract_known_cookies_from_db("/home/christian/Desktop/crawl1.sqlite", extracted)
    id_clusters =  cluster_domains_by_ids(known, "/home/christian/Desktop/crawl1.sqlite")
    G, colors = build_graph_from_id_clusters(id_clusters)
    nx.draw(G, node_color = colors)
    plt.show()
    
