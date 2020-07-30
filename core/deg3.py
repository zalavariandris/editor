import pythonflow as pf

with pf.Graph() as graph:
	a = pf.constant(4, name="a")
	b = pf.constant(38, name="b")
	x = pf.add(a,b, name="x")

res = graph(x)
print(res)

# class Node(object):
# 	def __init__(self, op):
# 		self.op = op

# 	def inputs(self):
# 		res = {}
# 		for i, op in enumerate(self.op.args):
# 			res[i] = op

# 		for key, op in self.op.kwargs.items():
# 			res[key] = op
# 		return res

	# def __repr__(self):
	# 	return "node"
	# 	return self.op.name

	# def __str__(self):
	# 	heading = "== '{}' ==".format(self.op.name)
	# 	content = "\n".join( ["- {}: {}".format(i, val.name if isinstance(val, pf.core.func_op) else val) for i, val in enumerate(self.op.args)] )
	# 	footer = ""

	# 	return heading+"\n"+content+"\n"+footer


from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
if __name__ == "__main__":
	from editor.widgets.nodeeditor import NodeEditor, Node, Edge, Socket
	app = QApplication.instance() or QApplication()
	editor = NodeEditor()


	operations = graph.operations
	# create nodes
	for name, op in operations.items():
		# create node
		node = Node(name=name)
		editor.addNode(node)

		# add input pins
		for i, dep in enumerate(op.args):
			if isinstance(dep, pf.core.func_op):
				node.addInput(Socket(""))

		for k, dep in op.kwargs.items():
			if isinstance(dep, pf.core.func_op):
				node.addInput(Socket(k))

		# add output pins
		node.addOutput(Socket(""))

	# create edges
	for op in operations:
		print(op.args)
		
	editor.show()
	app.exec_()

