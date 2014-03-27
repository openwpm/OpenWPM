function hover_node(e) {
	console.log(e.data.node.color);
	e.data.node.color = "eeeeee";
	s.refresh();
}