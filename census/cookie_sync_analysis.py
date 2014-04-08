import measure_cookie_sync
import extract_cookie_ids
import measure_cookie_sync
import networkx as nx
import numpy

# get an array of sorted cookie counts
def get_cookie_counts(G):
    cookie_counts = {}
    for node in G.nodes():
        cookies = G.node[node]['cookies']
        for cookie in cookies:
            if cookie not in cookie_counts:
                cookie_counts[cookie] = 1
            else:
                cookie_counts[cookie] += 1
    
    counts = []
    for cookie in cookie_counts:
        counts.append(cookie_counts[cookie])
    
    counts.sort()
    return counts

# gets a tuple of the form (node, degree)
def print_degree_stats(deg_tuples):
    deg_tuples = sorted(deg_tuples, key=lambda tup: tup[1])
    degs = [tup[1] for tup in deg_tuples]
    print "avg. = " + str(numpy.mean(degs))
    print "(min, quarter, median, 3/4, max) = " + str((degs[0], degs[int(0.25 * len(degs))], degs[int(0.50 * len(degs))], degs[int(0.75 * len(degs))], degs[len(degs)-1]))
    print "TOP 20 nodes"
    for i in xrange(max([0, len(deg_tuples) - 20]), len(deg_tuples)):
        print str(deg_tuples[i])
    

# This is a set of analysis tools for cookie sync
def print_graph_statistics(G):
    print "|V| = " + str(len(G.nodes()))
    print "|E| = " + str(len(G.edges()))

    # weakly connected components stats
    wcc = nx.weakly_connected_components(G)
    print "|WCC| = " + str(len(wcc))
    print "|Biggest WCC| = " + str(max([len(c) for c in wcc]))

    # strongly connected component stats
    scc = nx.strongly_connected_components(G)
    print "|SCC| = " + str(len(scc))
    print "|Biggest SCC| = " + str(max([len(c) for c in scc]))

    # Cookie Data
    counts = get_cookie_counts(G)
    print "|cookies| = " + str(len(counts))
    print "avg. cookie spread = " + str(numpy.mean(counts))
    print "Cookie (min, quarter, median, 3/4, max) = " + str((counts[0], counts[int(0.25 * len(counts))], counts[int(0.50 * len(counts))], counts[int(0.75 * len(counts))], counts[len(counts)-1]))

    # Cookie Owners
    print "cookie owners"
    owners = [(node, len(G.node[node]['cookies'])) for node in G.nodes()]
    print_degree_stats(owners)

    # Degree analysis
    print "Out degree analysis"
    outs = [(node, G.out_degree(node)) for node in G.nodes()]
    print_degree_stats(outs)

    print "In degree analysis"
    ins = [(node, G.in_degree(node)) for node in G.nodes()]
    print_degree_stats(ins)

    print "Degree analysis"
    degs = [(node, G.degree(node)) for node in G.nodes()]
    print_degree_stats(degs)

if __name__ == "__main__":
    print "READING DB1"
    c1 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/alexa1.sqlite")
    print "READING DB2"
    c2 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/christian/Desktop/alexa2.sqlite")
    print "EXTRACTING COOKIES"
    extracted = extract_cookie_ids.extract_common_persistent_ids([c1, c2])
    print "BUILDING GRAPH"
    G = measure_cookie_sync.build_sync_graph("/home/christian/Desktop/alexa1.sqlite", extracted)
    print "GRAPH BUILT"
    print_graph_statistics(G)
    

