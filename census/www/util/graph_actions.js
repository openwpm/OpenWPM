var curr_clicked = null;  // currently clicked node
var curr_cookies = null;  // list of cookies held at currently clicked node
var highlighted = "ffff00";  // color to highlight node

// dummy function: colors a node gray
function hover_node(n) {
    // either we are not clicking on a node or we are hovering over that node
    // also, ignore nodes that are not currently highlighed
    if (curr_clicked == null || n.data.node.id == curr_clicked || n.data.node.color != highlighted) {
        return;
    }

    // try fo find the common cookies
    common_cookies = [];
    curr_cookies.forEach(function (c) {
        if (c in n.data.node.cookies) {
            common_cookies.push(c);
        }
    });
    
    common_cookies.sort();
    console.log(common_cookies);
    
    
    //e.data.node.color = "eeeeee";
    s.refresh();
}

function click_stage(stage) {
    reset_settings(stage);
    s.refresh();
}

// sets the graph to its original coloring
function reset_settings(stage) {
    s.graph.nodes().forEach(function(n) {
        n.color = n.original_color;
    });
    s.graph.edges().forEach(function(e) {
        e.color = e.original_color;
    });
}

function click_node(e) {
    if (e.data.node.id == curr_clicked) {
        return;
    }
    reset_settings(e);
    color_flow(e);
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
                n.color = highlighted;
            }
        });
    });

    // next, color the edges
    s.graph.edges().forEach(function(e) {
        cookies.some(function(c) {
            if (c in e.cookies) {
                e.color = highlighted;
            }
        });
    });
    s.refresh();
}
