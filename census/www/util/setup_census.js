var node_color = "0066ff";  // standard color for nodes
var tp_color = "e06666";  // color for third-party nodes 
var color_tp = false; // should we be coloring third-party nodes
var edge_color = "999999";  // standard color for edges
var faded = "fffaf0";  // color for faded out parts of the graph
var highlighted = "cc8400"; // color to highlight a node (usually the one clicked)
var curr_weight;  // the current weight for nodes to be drawn in accordance with slider
var curr_clicked = null;  // the node that we have currently clicked
var curr_cookies = null;  // the list of cookies owned by the currently-clicked node
var curr_hovered = null;  // the currently hovered-over node
var node_to_index = {};  // dictionary that maps nodes names to indices
var default_zoom_level; // baseline ui ratio
var zoom_ratio = 0.8; // ratio in which zoom bar moves
var num_trackers = 20; // the number of top trackers we wish to display

// omnibus initialization function that builds up our Sigma.JS graph
// and also sets up the various UI components
function init() {
	// setup the graph by parsing the json file
	s = new sigma({
        container: document.getElementById('graph'),
        settings: {
            'labelThreshold' : 10, // ensures that no labels are drawn to begin
            'doubleClickZoomingRatio' : 1  // for now, stops double clicking
        }
    });

    // read in the graph
	sigma.parsers.json(
		'graph.json',
		s,
        // performs the graph pre-processing and sets up the ui
        function() {
            max_weight = 0;  // the weight of the node that knows the most IDs

            // sets the colors, weights and draw_sizes for the nodes
            // calculates the maximum weight of a nodes
            // also, adds a to_draw boolean that 
            // nodes will be drawn if to_draw and weight threshold passes
            s.graph.nodes().forEach(function(n) {
                n.color = node_color;
                n.hidden = false;
                n.size = 5;
                n.to_draw = true;
                n.label = n.id;
                if (n.weight > max_weight) {
                    max_weight = n.weight;
                }
            });

            // next, set the colors and weights for edges
            // for now, edge weights are not being used
            s.graph.edges().forEach(function(e) {
                e.color = edge_color;
                e.hidden = false; 
                e.weight = Object.keys(e.cookies).length;
            });
			s.refresh();

            // INFOGRAPHIC: flag the top 20 trackers
            // get a list of top trackers sorted by descending weights (ties done alphabetically)
            top_trackers = s.graph.nodes().sort(
                function(a,b) {
                    if (a.weight == b.weight) {
                        return a.id.localeCompare(b.id);
                    }
                    return b.weight - a.weight;
                }
            );

            // next, build the actual table and save it in the table element
            tracker_table = "<table>"
            for (var i = 0; i < num_trackers; i++) {
                tracker_table += "<tr><td><a onclick=select_node(top_trackers["+ i +"])>" + top_trackers[i].id + "</a></td>";
                tracker_table += "<td>" + top_trackers[i].weight + "</td></tr>";
            }
            tracker_table += "</table>"
                
            $("#top_trackers").html(tracker_table);

            // UI 1: build button to toggle third-party coloring
            $("#toggle_tp").button().click(function(e) {
                color_tp = (color_tp != true); // flips the bit (no JS XOR) for coloring tps
                redraw_graph();
            });

            // UI 2: build up a slider that filters nodes by weights

            // sets an arbitrary starting weight (max/2 seems to highlight the main TPs)
            starting_weight = Math.floor(max_weight / 2);
            curr_weight = starting_weight;  // starting weight is our baseline filtering level
            $("#cookie_weight").html(starting_weight)
            $("#weight_slider").slider({
                range: "max",
                min: 1,
                max: max_weight,
                value: starting_weight,

                // when sliding to a new value, re-color the graph based on weights
                // also, updates the UI element itself
                slide: function(event, ui) {
                    $("#cookie_weight").html(ui.value);

                    curr_weight = ui.value;
                    redraw_graph();
                }
            });
            // draw the graph based on the initial starting weights
            redraw_graph(); 

            // UI 3: build a slider for zooming in and out of the graph
            default_zoom_level = 4;
            $("#zoom_slider").slider({
                range: "max",
                min: 0,
                max: 7,
                value: default_zoom_level,
                
                // causes the graph to grow or shrink in size
                slide: function(event, ui) {
                    s.cameras[0].ratio = Math.pow(zoom_ratio, ui.value - default_zoom_level);
                    s.refresh();
                }
            });

            // UI 4: build an autocomplete feature that highlights nodes that know that cookie ID
            
            // first, builds up a list of all the cookies onwed by the nodes
            // also, build up a list of all the sites
            cookie_dict = {};
            s.graph.nodes().forEach(function(n) {
                Object.keys(n.cookies).forEach(function(c) {
                    cookie_dict[c] = true;
                });
            });
            cookie_list = Object.keys(cookie_dict);
            cookie_list.sort();

            // initialize the autocomplete with this list of known cookies
            $("#cookie_search").autocomplete({
                source: cookie_list,

                // highlights all sites that know the given cookie ID
                select: function(event, ui) {
                    $("#site_search").val("");
                    highlight_cookie_owners(ui.item.value);
                }
            });

            // UI 5: build an autocomplete feature that allows you to select a site to highlight (like clicking)

            // first, process the list of sites we just collected, then build the autocomplete feature
            sites = [];
            index = 0;
            s.graph.nodes().forEach(function(n) {
                sites.push(n.id);
                node_to_index[n.id] = index;
                index++;
            });
            sites.sort();

            $("#site_search").autocomplete({
                source: sites,

                select: function(event, ui) {
                    select_node(s.graph.nodes()[node_to_index[ui.item.value]]);
                }
            });
            
    });

    // bind graph actions to actions in graph_actions.js
    s.bind('doubleClickStage', click_stage);
    s.bind('clickNode', click_node);
    s.bind('overNode', hover_node);
    s.bind('outNode', unhover_node);
}
