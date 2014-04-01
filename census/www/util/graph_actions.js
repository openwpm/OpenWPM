var curr_clicked = null;  // currently clicked node
var curr_cookies = null;  // list of cookies held at currently clicked node

// dummy function: colors a node gray
function hover_node(n) {
    // either we are not clicking on a node or we are hovering over that node
    // also, ignore nodes that are not currently highlighed
    if (curr_clicked == null || n.data.node.id == curr_clicked || n.data.node.color != node_color) {
        return;
    }

    // try to find the common cookies
    common_cookies = [];
    curr_cookies.forEach(function (c) {
        if (c in n.data.node.cookies) {
            common_cookies.push(c);
        }
    });
    
    common_cookies.sort();
    console.log(common_cookies);
    fill_cookie_data(n.data.node.id);
    
    s.refresh();
}

function unhover_node(n) {
    if (curr_clicked == null) {
        return;
    }

    fill_cookie_data(null);
}

function click_stage(stage) {
    reset_settings(stage);
    s.refresh();
}

// sets the graph to its original coloring
function reset_settings(stage) {
    $("#cookie_panel").hide();
    s.graph.nodes().forEach(function(n) {
        if (n.weight < curr_weight) {
            n.color = faded;
        }
        else {
            n.color = node_color;
        }
    });

    s.graph.edges().forEach(function(e) {
         if (s.graph.nodes(e.source).color == faded 
            || s.graph.nodes(e.target).color == faded) {
            e.color = faded;
        }
        else {
            e.color = edge_color;
        }
    });
}

function click_node(e) {
    if (e.data.node.id == curr_clicked) {
        return;
    }

    color_flow(e);
    $("#cookie_panel").show()
    fill_cookie_data(null);
}

// used for clicking, colors all nodes and edges that share a common cookie
// with the currently clicked node
function color_flow(e) {
    // gets the cookies placed at this node
    cookies = Object.keys(e.data.node.cookies);
    curr_clicked = e.data.node.id;
    curr_cookies = cookies;

    // color all nodes that have a cookie shared with this node
    s.graph.nodes().forEach(function(n) {
        cookies.some(function(c) {
            if (c in n.cookies) {
                n.color = node_color;
            }
            else {
                n.color = faded;
            }
        });
    });

    // next, color the edges
    s.graph.edges().forEach(function(e) {
        cookies.some(function(c) {
            if (c in e.cookies) {
                e.color = edge_color;
            }
            else {
                e.color = faded;
            }
        });
    });
    s.refresh();
}

function fill_cookie_data(hovered_node) {
    if (hovered_node == null) {
        msg = "<b>ID cookies known by: "  +s.graph.nodes(curr_clicked).label + "</b>";
        $("#owners").html("<b>ID cookies known by: " +s.graph.nodes(curr_clicked).label + "</b>");
        // in this case, we fill in all of the current cookies
        owned_cookies = "";
        curr_cookies.forEach(function(c) {
            owned_cookies += c + "</br>";
        });

        $("#cookies").html(owned_cookies);
    }

    else {
        console.log(s.graph.nodes(hovered_node).label);
        msg = "<b>ID cookies jointly known by: " + s.graph.nodes(curr_clicked).label;
        msg += " and " + s.graph.nodes(hovered_node).label
        $("#owners").html(msg);

        owned_cookies = "";
        curr_cookies.forEach(function(c) {
            if (c in s.graph.nodes(hovered_node).cookies) {
                owned_cookies += c + "</br>";
            }
        });

        $("#cookies").html(owned_cookies);
    }
}

function filter_out_low_weights(threshold_weight) {
    // first fade out the low-weight nodes
    s.graph.nodes().forEach(function(n) {
        if (n.weight < threshold_weight) {
            n.color = faded;
        }
        else {
            n.color = node_color;
        }
    });

    // next, fade out the edges with at least one faded node
    s.graph.edges().forEach(function(e) {
        if (s.graph.nodes(e.source).color == faded 
            || s.graph.nodes(e.target).color == faded) {
            e.color = faded;
        }
        else {
            e.color = edge_color;
        }
    });
    s.refresh();
}

function highlight_cookie_owners(cookie) {
    // highlight only the nodes and edges with a single value
    s.graph.nodes().forEach(function(n) {
        if (cookie in n.cookies) {
            n.color = node_color;
        }
        else {
            n.color = faded;
        }
    });
    // next, highlight the edges with a single value
    s.graph.edges().forEach(function(e) {
        if (cookie in e.cookies) {
            e.color = edge_color;
        }
        else {
            e.color = faded;
        }
    });
    s.refresh();
}
