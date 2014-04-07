// library of actions used for interacting with the cookie graph

// DRAWING UTILITY FUNCTIONS

// sets all nodes to be drawable
function set_all_drawable() {
    s.graph.nodes().forEach(function(n) { 
        n.to_draw = true;
    });
}

// re-colors and draws the weighted graph
// draws a node n if n.to_draw and n.weight > curr_weight
// draws an edge if both of its endpoints are drawn
function redraw_graph() {
    // re-color the nodes
    s.graph.nodes().forEach(function(n) {
        if (!n.to_draw || n.weight < curr_weight) {
            n.color = node_color;
            n.hidden = true;
        }
        else {
            n.hidden = false;
            n.color = node_color;
            if (n.id == curr_clicked) {
                n.color = highlighted;
            }
        }
    });

    // re-color the edges
    s.graph.edges().forEach(function(e) {
        if (s.graph.nodes(e.source).hidden
            || s.graph.nodes(e.target).hidden) {
            e.hidden = true;
        }
        else {
            e.hidden = false;
        }
    });

    // re-render the graph
    s.refresh();
}

// UI-DRIVEN FUNCTIONS

// sets the nodes who know the cookie <cookie> to_draw then draw the grpah
function highlight_cookie_owners(cookie) {
    s.graph.nodes().forEach(function(n) {
        if (cookie in n.cookies) {
            n.to_draw = true;
        }
        else {
            n.to_draw = false;
        }
    });
    
    redraw_graph();
}

// GRAPH-CLICK-DRIVEN FUNCTIONS

// after clicking on the stage, resets the graph
// unselects the clicking and resets the ui
function click_stage(stage) {
    curr_clicked = null;
    curr_cookies = null;

    $("#cookie_panel").hide();
    $("#cookie_search").val("");
    $("#site_search").val("");

    set_all_drawable();
    redraw_graph();
}

// function when you click on a node
// set the node and nodes that mutually know at least one common id to be drawn
function click_node(clicked) {
    select_node(clicked.data.node);
}

function select_node(selected) {
    // only act if not already clicked on this node before
    if (selected.id == curr_clicked) {
        return;
    }
    
    // update the autocomplete for completeness
    $("#site_search").val(selected.id);

    // reset ids and get sorted list of cookies
    curr_clicked = selected.id;
    cookies = Object.keys(selected.cookies);
    cookies.sort();
    curr_cookies = cookies;

    // color all nodes that have a cookie shared with this node
    s.graph.nodes().forEach(function(n) {
        // determines if n knows the same cookie as curr_clicked
        shares_common = cookies.some(function(c) {
            if (c in n.cookies) {
                return true;
            }
        });

        if (shares_common) {
            n.to_draw = true;
        }
        else {
            n.to_draw = false;
        }
    });
    redraw_graph();

    // re-set the cookie panel
    $("#cookie_panel").show();
    fill_known_cookie_data(null);
}

// function when we hover over a node
// 
function hover_node(hovered) {
    // either we are not clicking on a node or we are hovering over that node
    // also, ignore nodes that are not currently highlighed
    if (curr_clicked == null || hovered.data.node.id == curr_clicked || hovered.data.node.hidden) {
        return;
    }

    curr_hovered = hovered.data.node.id;
    fill_known_cookie_data(hovered.data.node.id);
}

// function when we no longer hover on the currently-hovered node
// reset the jointly-known cookie list to a single owner
function unhover_node(n) {
    if (curr_clicked == null || n.data.node.id != curr_hovered) {
        return;
    }

    curr_hovered = null;
    fill_known_cookie_data(null);
}

// helper function used to fill in side panel about the sites that know particular ids
// two cases: we are not hovering over a node (in which case, we only care about the currently-clicked site)
// otherwise, we wish to know the joinly-known IDs
function fill_known_cookie_data(hovered_node) {
    // i.e. we are not hovering over a particular cookie
    if (hovered_node == null) {
        msg = "<b>Cookie IDs known by " + s.graph.nodes(curr_clicked).label + ":</b>";
        $("#owners").html("<b>ID cookies known by: " +s.graph.nodes(curr_clicked).label + "</b>");

        // build the list of all cookies known by curr_site
        owned_cookies = "";
        curr_cookies.forEach(function(c) {
            owned_cookies += c + "</br>";
        });

        $("#cookies").html(owned_cookies);
    }

    // i.e. we are hovering over a given node <hovered_node>
    else {
        msg = "<b>Cookie IDs jointly known by " + s.graph.nodes(curr_clicked).label;
        msg += " and " + s.graph.nodes(hovered_node).label + "</b>";
        $("#owners").html(msg);

        // buils the list of all jointly-known cookies
        owned_cookies = "";
        curr_cookies.forEach(function(c) {
            if (c in s.graph.nodes(hovered_node).cookies) {
                owned_cookies += c + "</br>";
            }
        });

        $("#cookies").html(owned_cookies);
    }
}
