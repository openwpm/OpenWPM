var node_color = "0066ff";  // standard color for nodes
var edge_color = "999999"; // standard color for edges
var faded = "fffaf0"; // color for faded out parts of the graph
var curr_weight;

function init() {
	// setup the graph
	s = new sigma(document.getElementById('graph'));
	sigma.parsers.json(
		'graph.json',
		s,
		function() {
            max_weight = 0; // max weight of a node

            // save the original color of the graph for later re-coloring
            // also, save the weights for each node and edge
            s.graph.nodes().forEach(function(n) {
                n.color = node_color;
                n.original_color = n.color;
                n.weight = Object.keys(n.cookies).length;
                n.size = 1;
                if (n.weight > max_weight) {
                    max_weight = n.weight;
                }
            });
            s.graph.edges().forEach(function(e) {
                e.color = edge_color;
                e.original_color = e.color;
                e.weight = Object.keys(e.cookies).length;
            });
			s.refresh();

            // ui, pt 1: build up a slider that filters nodes by weights
            starting_weight = Math.floor(max_weight / 4);
            curr_weight = starting_weight;
            $("#cookie_weight").html(starting_weight)
            $("#weight_slider").slider({
                range: "max",
                min: 1,
                max: max_weight,
                value: starting_weight,
                slide: function(event, ui) {
                    curr_weight = ui.value;
                    $("#cookie_weight").html(ui.value);
                    filter_out_low_weights(ui.value);
                }
            });
            filter_out_low_weights(starting_weight);
            curr_weight = starting_weight;

            // ui, pt 2: build up an autocomplete feature to look up cookies
            // first get the list of all the cookies
            cookie_dict = {};
            s.graph.nodes().forEach(function(n) {
                Object.keys(n.cookies).forEach(function(c) {
                    cookie_dict[c] = true;
                });
            });
            cookie_list = Object.keys(cookie_dict);
            cookie_list.sort();
            $("#cookie_search").autocomplete({
                source: cookie_list,
                select: function(event, ui) {
                    highlight_cookie_owners(ui.item.value);
                }
            })
    });
          
	// bind actions from graph_actions.js
	s.bind('overNode', hover_node);
    s.bind('outNode', unhover_node);
    s.bind('clickStage', click_stage);
    s.bind('clickNode', click_node);
}
