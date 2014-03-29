var base_color = "ff0000";

function init() {
	// setup the graph
	s = new sigma(document.getElementById('graph'));
	sigma.parsers.json(
		'graph.json',
		s,
		function() {
            // save the original color of the graph for later re-coloring
            s.graph.nodes().forEach(function(n) {
                n.color = base_color;
                n.original_color = n.color;
            });
            s.graph.edges().forEach(function(e) {
                e.color = base_color;
                e.original_color = e.color;
            });
			s.refresh();
		}
	);

	// bind actions from graph_actions.js
	s.bind('overNodes', hover_node);
    s.bind('outNode', unhover_node);
    s.bind('clickStage', click_stage);
    s.bind('clickNode', click_node);
   
}
