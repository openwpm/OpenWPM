function init() {
	// setup the graph
	s = new sigma(document.getElementById('graph'));
	sigma.parsers.json(
		'graph.json',
		s,
		function() {
            // save the original color of the graph for later re-coloring
            s.graph.nodes().forEach(function(n) {
                n.original_color = n.color;
            });
            s.graph.edges().forEach(function(e) {
                e.original_color = e.color;
            });
			s.refresh();
		}
	);

	// bind actions from graph_actions.js
	s.bind('overNode', hover_node);
    s.bind('clickStage', click_stage);
    s.bind('clickNode', click_node);
   
}
