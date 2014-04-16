import networkx as nx
import extract_cookie_ids
import sqlite3 as lite
import census_util
import sigma_graph_json
from sets import Set

# builds and returns a cookie synchronization graph
# nodes are websites and (directed) edges illustrate cookie values flowing between sites
# each node and edge contains the cookies that are available to them
# only includes cookies in the graph that are present in at least 1 transfer
def unique(seq):
    # Not order preserving
    return {}.fromkeys(seq).keys()

def build_sync_graph(db_name, known_cookies):
    # first, build a dictionary that maps cookies to the value actually seen in the database
    value_dict = extract_cookie_ids.extract_known_cookies_from_db(db_name, known_cookies)
    g = nx.DiGraph()  # cookie flow graph

    con = lite.connect(db_name)
    cur = con.cursor()

    # iterates through all the cookie ids to look from them flowing throughout the graph
    edge_list = list()
    for url, referrer in cur.execute('SELECT DISTINCT url, referrer FROM http_requests'):
        referrer = census_util.extract_domain(referrer)
        short_url = census_util.extract_domain(url)
        
        for cookie in value_dict:
            if cookie[0] == '':
                continue

            if value_dict[cookie] in url:
                cookie_str = str(cookie[0]) + " " + str(cookie[1])
                edge_list.append((referrer, short_url, cookie_str))
                break #NOTE will IDs ever change?

    #do it as a vector -- should be possible and must faster
    #g.add_edges_from(edge_list, cookies={})

    #add the unique triplets to graph
    edge_list = unique(edge_list)
    for item in edge_list:
        g.add_node(item[0], cookies={})
        g.add_node(item[1], cookies={})
        g.add_edge(item[0], item[1], cookies={})
        g.edge[item[0]][item[1]]['cookies'][item[2]] = 1
        g.node[item[0]]['cookies'][item[2]] = 1
        g.node[item[1]]['cookies'][item[2]] = 1
                
    return g

# takes in a graph and adds fields to it to make it drawable in sigma.js
# also, takes in a site file, which is a list of sites used to tag whether a site is FP or TP
def add_drawable_graph_fields(G, site_file):
    # remove blank node if necessary
    if '' in G.nodes():
        G.remove_node('')
        layout = nx.spring_layout(G)

    # adds coordinates to node
    for node in layout:
        G.add_node(node, x=float(layout[node][0]), y=float(layout[node][1]))

    # builds a set of known first parties
    fp = Set()
    f = open(site_file)
    for line in f:
        fp.add(line.strip())
    f.close()

    # goes through the graph, if node in the set of fp, tag it as a first party - otherwise first party
    for node in G.nodes():
        if node in fp:
            G.node[node]['third_party'] = 0
        else:
            G.node[node]['third_party'] = 1

    # calculates the weight for a node: defined as the number of unique domains that a third party exposes
    for node in G.nodes():
        G.node[node]['weight'] = get_unique_cookie_domains(G.node[node]['cookies'])

    return G

# returns the number of distinct top-level domains that a given party owns
# so that here.example.com and there.example.com are not double-counted for instance
def get_unique_cookie_domains(cookie_dict):
    domains = Set()

    for cookie in cookie_dict:
        domain = cookie.split()[0].strip()
        domain = domain if domain.startswith("http") else "http://" + domain # hack since http utils require url to start with http
        domains.add(census_util.extract_domain(domain))

    return len(domains)
    

if __name__ == "__main__":
    c1 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/crawl1.sqlite")
    c2 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/crawl2.sqlite")
    extracted = extract_cookie_ids.extract_common_persistent_ids([c1, c2])
    known = extract_cookie_ids.extract_known_cookies_from_db("/home/christian/Desktop/crawl1.sqlite", extracted)
    G = build_sync_graph("/home/christian/Desktop/crawl1.sqlite", extracted)
    G = add_drawable_graph_fields(G, "alexa.txt")
    sigma_graph_json.write_json_graph_to_file(G, "/home/christian/Desktop/graph.json")

