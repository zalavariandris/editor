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

from editor.widgets.graphwidget import GraphWidget, GraphWidgetNodeItem, GraphWidgetEdgeItem, GraphWidgetSocketItem


class Window(QMainWindow):
    def __init__(self, graph, sources={}):
        super().__init__(parent=None)
        assert isinstance(graph, pf.Graph)
        assert set(sources.keys()) == {name for name, op in graph.operations.items() if isinstance(op, pf.placeholder)}

        self.setWindowTitle("pythonflow-editor")
        self.graph = graph

        self._selection = []
        self.graphWidget = GraphWidget()
        self.setCentralWidget(self.graphWidget)

        self.graphWidget.scene.selectionChanged.connect(lambda: self.setSelection( {node.op for node in self.graphWidget.scene.selectedItems()} ))
        
        self.nodes = {} # store nodes for each operator


        self.initGraph(sources)

    def nodeData(self, index, role=Qt.DisplayRole):
        op, column = index
        if role is Qt.DisplayRole:
            if column is "name":
                return op.name
            elif column is "klass":
                if type(op)==pf.operations.func_op:
                    return op.target.__name__
                else:
                    return str( op.__class__.__name__ )
        return None

    def inputsForNode(self, op):
        """
        return the pin index
        pin index is compised of the operator and
        the positional or named argument
        """
        for i, dep in enumerate(op.args):
            if isinstance(dep, pf.core.func_op) or isinstance(dep, pf.placeholder):
                yield dep

    def outputsForNode(self, op):
        return [None]

    def initGraph(self, sources):
        # create nodes
        for name, op in list(graph.operations.items()):
                   
            node = GraphWidgetNodeItem(name="{} ({})".format( self.nodeData((op, "name")) , self.nodeData((op, "klass")) ))
            node.op = op

            for port in self.inputsForNode(op):
                node.addInput(GraphWidgetSocketItem(""))

            for port in self.outputsForNode(op):
                node.addOutput(GraphWidgetSocketItem(""))

            if isinstance(op, pf.placeholder):
                slider = QGraphicsProxyWidget()
                slider.setWidget(QSlider(Qt.Horizontal))
                node._outputs[0].layout().insertItem(0,slider)

                slider.widget().setValue(sources[op.name])
                slider.widget().valueChanged.connect(lambda value: self.setGraphSource(op.name, value))

            # add node to the window
            self.graphWidget.addNode(node)
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

                    edge = GraphWidgetEdgeItem(outputPin, inputPin)
                    self.graphWidget.addEdge(edge)

            for key, dep in op.kwargs.items():
                isOp = isinstance(dep, pf.Operation)
            
        self.graphWidget.graph.layout()
        self.graphWidget.centerOn(self.graphWidget.graph)

        self.evaluateGraph(sources)

    def evaluateGraph(self, sources):
        @contextlib.contextmanager
        def syncNode(operation, context):
            yield
            node = self.nodes[operation]
            output = context[operation]
            text = str(output)
            print(text)
            node._outputs[0].setText(str(output))

        self.graph(self.graph.operations['x'], callback=syncNode, **sources)

    def getGraphSources(self):
        sources = {}
        for op, node in self.nodes.items():
            if isinstance(op, pf.placeholder):
                slider = node.layout().itemAt(1).layout().itemAt(1).layout().itemAt(0).layout().itemAt(0).widget()
                sources[op.name] = slider.value()
        return sources

    def setSelection(self, selection):
        assert isinstance(selection, set)

        def syncGraphWidgetSelection():
            print("sync editor selection")
            oldState = self.graphWidget.scene.blockSignals(True)
            for op, node in self.nodes.items():
                isOpSelected = id(op) in {id(_) for _ in selection}
                isNodeSelected = node.isSelected()
                if isOpSelected != isNodeSelected:
                    node.setSelected(isOpSelected)

            self.graphWidget.scene.blockSignals(oldState)

        syncGraphWidgetSelection()

    def setGraphSource(self, name, value):
        sources = self.getGraphSources()
        self.evaluateGraph(sources)


if __name__ == "__main__":
    app = QApplication.instance() or QApplication()
    window = Window(graph, {'a': 90, 'b': 30})
    window.show()
    app.exec_()

