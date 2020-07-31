import pythonflow as pf


class PFSlider(pf.placeholder):
    pass

with pf.Graph() as graph:
    a = PFSlider(name="a")
    b = PFSlider(name="b")
    x = (a*b).set_name("x")

# print(res)


from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


import contextlib

from editor.widgets.nodeeditor import NodeEditor, Node, Edge, Socket


class Window(QMainWindow):
    def __init__(self, graph, sources={}):
        super().__init__(parent=None)
        assert isinstance(graph, pf.Graph)
        assert set(sources.keys()) == {name for name, op in graph.operations.items() if isinstance(op, pf.placeholder)}

        self.setWindowTitle("pythonflow-editor")
        self.graph = graph

        self._selection = []
        self.nodeeditor = NodeEditor()
        self.setCentralWidget(self.nodeeditor)

        self.nodeeditor.scene.selectionChanged.connect(lambda: self.setSelection( {node.op for node in self.nodeeditor.scene.selectedItems()} ))
        
        self.nodes = {} # store nodes for each operator


        self.initGraph(sources)

    def evaluate(self, sources):
        print(sources)
        self.graph(self.graph.operations['x'], callback=self.onEvaluate, **sources)

    def getSources(self):
        sources = {}
        for op, node in self.nodes.items():
            if isinstance(op, pf.placeholder):
                slider = node.layout().itemAt(1).layout().itemAt(1).layout().itemAt(0).layout().itemAt(0).widget()
                sources[op.name] = slider.value()
        return sources

    def setSelection(self, selection):
        assert isinstance(selection, set)

        def syncNodeEditorSelection():
            print("sync editor selection")
            oldState = self.nodeeditor.scene.blockSignals(True)
            for op, node in self.nodes.items():
                isOpSelected = id(op) in {id(_) for _ in selection}
                isNodeSelected = node.isSelected()
                if isOpSelected != isNodeSelected:
                    node.setSelected(isOpSelected)

            self.nodeeditor.scene.blockSignals(oldState)

        syncEditorSelection()

    @contextlib.contextmanager
    def onEvaluate(self, operation, context):
        yield
        node = self.nodes[operation]
        output = context[operation]
        text = str(output)
        print(text)
        node._outputs[0].setText(str(output))

    def setSource(self, name, value):
        sources = self.getSources()
        self.evaluate(sources)

    def initGraph(self, sources):
        # create nodes
        for name, op in list(graph.operations.items()):
            # create node
            def nodeTitle():
                name = op.name

                if type(op)==pf.operations.func_op:
                    klass = op.target.__name__
                else:
                    klass = str( op.__class__.__name__ )
                return "{} ({})".format(name, klass)

            def nodeInputs():
                for i, dep in enumerate(op.args):
                    if isinstance(dep, pf.core.func_op) or isinstance(dep, pf.placeholder):
                        yield Socket("")

            def nodeOutputs():
                if isinstance(op, PFSlider):
                    socket = Socket("")
                    yield socket
                else:
                    yield Socket("")
                    
            node = Node(name=nodeTitle())
            node.op = op
            for socket in nodeInputs():
                node.addInput(socket)

            for socket in nodeOutputs():
                node.addOutput(socket)

            if isinstance(op, pf.placeholder):
                slider = QGraphicsProxyWidget()
                slider.setWidget(QSlider(Qt.Horizontal))
                node._outputs[0].layout().insertItem(0,slider)

                slider.widget().setValue(sources[op.name])
                slider.widget().valueChanged.connect(lambda value: self.setSource(op.name, value))

            # add node to the window
            self.nodeeditor.addNode(node)
            self.nodes[op] = node

        # link node with edges
        for name, op in graph.operations.items():
            for i, dep in enumerate(op.args):
                isOp = isinstance(dep, pf.Operation)
                if isOp:
                    dst = self.nodes[op]
                    src = self.nodes[dep]
                    outputPin = src._outputs[0]
                    inputPin = dst._inputs[i]

                    edge = Edge(outputPin, inputPin)
                    self.nodeeditor.addEdge(edge)

            for key, dep in op.kwargs.items():
                isOp = isinstance(dep, pf.Operation)
            
        self.nodeeditor.graph.layout()
        self.nodeeditor.centerOn(self.nodeeditor.graph)

        self.evaluate(sources)


if __name__ == "__main__":
    app = QApplication.instance() or QApplication()
    window = Window(graph, {'a': 90, 'b': 30})
    window.show()
    app.exec_()

