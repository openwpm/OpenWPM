# Sigma.JS requires a very specific JSON format for its graphs
# The various python-based graph serialization libraries seem to fail for networkx graph
# This module takes in such a graph and provides an accepted JSON serialization
# TODO: add support for directed graphs

def build_node(G, node):
    val = {
    "id": str(node),
    "label": str(node),
    "x": G.node[node]['x'],
    "y": G.node[node]['y'],
    "cookies": G.node[node]['cookies']
    }
    return str(val).replace("\'", "\"")

# takes in an edge and a counter (i.e. the id for the edge)
# returns a string corresponding to the edge
def build_edge(G, edge, counter):
    val = {
        "id": "e" + str(counter),
        "source": str(edge[0]),
        "target": str(edge[1]),
        "cookies": G.edge[edge[0]][edge[1]]['cookies']
    }
    return str(val).replace("\'", "\"")

# Takes in a networkx graph
# Returns a json-encoded string
# Parsable by Sigma.JS
def build_json_encoding(G):
    json_parts = []

    json_parts.append("{\"nodes\": [")

    # Adds the encoded nodes
    counter = 0
    num_nodes = len(G.nodes())
    for node in G.nodes():
        counter += 1
        json_parts.append(build_node(G, node))
        if counter < num_nodes:
            json_parts.append(",")

    # Adds the encoded edges
    counter = 0
    num_edges = len(G.edges())
    json_parts.append("], \"edges\": [")
    for edge in G.edges():
        json_parts.append(build_edge(G, edge, counter))
        counter += 1
        if counter < num_edges:
            json_parts.append(",")


    json_parts.append("] }")

    return "".join(json_parts)

# takes in a for-now-undirected graph and dumps in to <file_name>
def write_json_graph_to_file(G, file_name):
    f = open(file_name, 'w')
    f.write(build_json_encoding(G))
    f.close()
