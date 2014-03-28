import networkx as nx
#import matplotlib.pyplot as plt
import extract_cookie_ids
import sqlite3 as lite
import census_util
import sigma_graph_json

# builds and returns a cookie synchronization graph
# nodes are websites and (directed) edges illustrate cookie values flowing between sites
# each node and edge contains the cookies that are available to them
# only includes cookies in the graph that are present in at least 1 transfer
def build_sync_graph(db_name, known_cookies):
    # first, build a dictionary that maps cookies to the value actually seen in the database
    value_dict = extract_cookie_ids.extract_known_cookies_from_db(db_name, known_cookies)
    g = nx.DiGraph()  # cookie flow graph

    con = lite.connect(db_name)
    cur = con.cursor()

    # iterates through all the cookie ids to look from them flowing throughout the graph
    for cookie in value_dict:
        query = 'SELECT url, referrer FROM http_requests WHERE url LIKE \'%' + value_dict[cookie] + '%\''
        for url, referrer in cur.execute(query):
            url = census_util.extract_domain(url)
            referrer = census_util.extract_domain(referrer)

            # adds edges and adds cookies to nodes + edges
            # TODO: error with blank strings?
            cookie_str = str(cookie[0]) + "|" + str(cookie[1])
            if url not in g:
                g.add_node(url, cookies={})
            if referrer not in g:
                g.add_node(referrer, cookies={})
            if (referrer, url) not in g.edges():
                g.add_edge(referrer, url, cookies={})

            g.edge[referrer][url]['cookies'][cookie_str] = 1
            g.node[referrer]['cookies'][cookie_str] = 1
            g.node[url]['cookies'][cookie_str] = 1

    # adds the weights to the nodes and edges
    # TODO: fix this, wrong under cookie dictionary scheme
    for node in g.nodes(data=True):
        g.node[node[0]]['weight'] = len(node[1])

    for edge in g.edges(data=True):
        g.edge[edge[0]][edge[1]]['weight'] = len(edge[2])

    return g

# takes in a graph and adds fields to it to make it drawable in sigma.js
def add_drawable_graph_fields(G):
    # remove blank node if necessary
    if '' in G.nodes():
        G.remove_node('')
        layout = nx.spring_layout(G)

    # adds coordinates to node
    for node in layout:
        G.add_node(node, x=float(layout[node][0]), y=float(layout[node][1]))

    return G

if __name__ == "__main__":
    c1 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/crawl1.sqlite")
    c2 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/crawl2.sqlite")
    extracted = extract_cookie_ids.extract_common_persistent_ids([c1, c2])
    known = extract_cookie_ids.extract_known_cookies_from_db("/home/christian/Desktop/crawl1.sqlite", extracted)
    G = build_sync_graph("/home/christian/Desktop/crawl1.sqlite", extracted)
    G = add_drawable_graph_fields(G)
    sigma_graph_json.write_json_graph_to_file(G, "/home/christian/Desktop/graph.json")

