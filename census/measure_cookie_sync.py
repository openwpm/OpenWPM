import networkx as nx
import matplotlib.pyplot as plt
import extract_cookie_ids
import sqlite3 as lite
import census_util

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
            g.add_edge(referrer, url)
            g.edge[referrer][url][cookie[0]] = cookie[1]
            g.node[referrer][cookie[0]] = cookie[1]
            g.node[url][cookie[1]] = cookie[1]

    # adds the weights to the nodes and edges
    for node in g.nodes(data=True):
        g.node[node[0]]['weight'] = len(node[1])

    for edge in g.edges(data=True):
        g.edge[edge[0]][edge[1]]['weight'] = len(edge[2])

    return g

if __name__ == "__main__":
    c1 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/crawl1.sqlite")
    c2 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/crawl2.sqlite")
    extracted = extract_cookie_ids.extract_common_persistent_ids([c1, c2])
    known = extract_cookie_ids.extract_known_cookies_from_db("/home/christian/Desktop/crawl1.sqlite", extracted)
    G = build_sync_graph("/home/christian/Desktop/crawl1.sqlite", extracted)
    nx.draw(G)
    plt.show()