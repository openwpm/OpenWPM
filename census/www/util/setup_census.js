var node_color = "0066ff";  // standard color for nodes
var edge_color = "999999";  // standard color for edges
var faded = "fffaf0";  // color for faded out parts of the graph
var curr_weight;  // the current weight for nodes to be drawn in accordance with slider
var curr_clicked = null;  // the node that we have currently clicked
var curr_cookies = null;  // the list of cookies owned by the currently-clicked node
var curr_hovered = null;  // the currently hovered-over node

// omnibus initialization function that builds up our Sigma.JS graph
// and also sets up the various UI components
function init() {
	// setup the graph by parsing the json file
	s = new sigma(document.getElementById('graph'));
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
                n.weight = Object.keys(n.cookies).length;
                n.size = 1;
                n.to_draw = true;
                if (n.weight > max_weight) {
                    max_weight = n.weight;
                }
            });

            // next, set the colors and weights for edges
            // for now, edge weights are not being used
            s.graph.edges().forEach(function(e) {
                e.color = edge_color;
                e.weight = Object.keys(e.cookies).length;
            });
			s.refresh();

            // UI 1: build up a slider that filters nodes by weights

            // sets an arbitrary starting weight (max/4 seems to highlight the main TPs)
            starting_weight = Math.floor(max_weight / 4);
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

            // UI 2: build an autocomplete feature that highlights nodes that know that cookie ID
            
            // first, builds up a list of all the cookies onwed by the nodes
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

                // performs an 
                select: function(event, ui) {
                    highlight_cookie_owners(ui.item.value);
                }
            })
    });
          
	// bind graph actions to actions in graph_actions.js
    s.bind('clickStage', click_stage);
    s.bind('clickNode', click_node);
    s.bind('overNode', hover_node);
    s.bind('outNode', unhover_node);
}
