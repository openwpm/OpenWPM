function init() {
	// setup the graph
	s = new sigma(document.getElementById('graph'));
	sigma.parsers.json(
		'graph.json',
		s,
		function() {
			s.refresh()
		}
	);

	// bind actions from graph_actions.js
	s.bind('overNode', hover_node)
}