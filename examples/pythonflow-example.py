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
# class SliderWidget(Node):
#     pass

class Delegate(QObject):
    commitData = Signal(QWidget, object)

    def createNode(self, op):
        print(op.graph)
        node = Node(name=self.nodeTitle(op))
        node.op = op
        for socket in self.nodeInputs(op):
            node.addInput(socket)

        for socket in self.nodeOutputs(op):
            node.addOutput(socket)

        if isinstance(op, pf.placeholder):
            slider = QGraphicsProxyWidget()
            slider.setWidget(QSlider(Qt.Horizontal))
            node._outputs[0].layout().insertItem(0,slider)
            slider.widget().valueChanged.connect(lambda: self.commitData.emit(node, op))

        return node

    def nodeTitle(self, op):
        name = op.name

        if type(op)==pf.operations.func_op:
            klass = op.target.__name__
        else:
            klass = str( op.__class__.__name__ )
        return "{} ({})".format(name, klass)

    def nodeInputs(self, op):
        for i, dep in enumerate(op.args):
            if isinstance(dep, pf.core.func_op) or isinstance(dep, pf.placeholder):
                yield Socket("")

    def nodeOutputs(self, op):
        if isinstance(op, PFSlider):
            socket = Socket("")
            yield socket
        else:
            yield Socket("")

    def setEditorData(self, window, node, value):
        # update editors (eg.: slider, graphics item) for placeholders
        # the pythonflow editor can edit pf.placeholder operations.
        # each placeholder can store one single arbitary data
        
        # value = op # get the placeholder value

        # print(window.sources[op.name], "args:", op.graph, op.name)
        node._outputs[0].layout().itemAt(0).widget().setValue(value)

    def setModelData(self, window, node, op):
        return editor.value
        print("set model data", editor.value(), op.name)


class Window(QMainWindow):
    def __init__(self, graph, sources={}):
        super().__init__(parent=None)
        assert isinstance(graph, pf.Graph)
        assert set(sources.keys()) == {name for name, op in graph.operations.items() if isinstance(op, pf.placeholder)}

        self.setWindowTitle("pythonflow-editor")
        self.graph = graph

        self._selection = []
        self.editor = NodeEditor()
        self.setCentralWidget(self.editor)

        self.editor.scene.selectionChanged.connect(lambda: self.setSelection( {node.op for node in self.editor.scene.selectedItems()} ))
        
        self.nodes = {} # store nodes for each operator

        self.delegate = Delegate()

        def on_source_change(editor, op):
            # self.delegate.setModelData(self, editor, op)
            sources = self.getSources()
            self.evaluate(sources)

        self.initGraph(sources)
        self.delegate.commitData.connect(on_source_change)

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

        def syncEditorSelection():
            print("sync editor selection")
            oldState = self.editor.scene.blockSignals(True)
            for op, node in self.nodes.items():
                isOpSelected = id(op) in {id(_) for _ in selection}
                isNodeSelected = node.isSelected()
                if isOpSelected != isNodeSelected:
                    node.setSelected(isOpSelected)

            self.editor.scene.blockSignals(oldState)

        syncEditorSelection()

    @contextlib.contextmanager
    def onEvaluate(self, operation, context):
        yield
        node = self.nodes[operation]
        output = context[operation]
        text = str(output)
        print(text)
        node._outputs[0].setText(str(output))

    def initGraph(self, sources):
        # create nodes
        for name, op in list(graph.operations.items()):
            # create node
            node = self.delegate.createNode(op)

            # add node to the window
            self.editor.addNode(node)
            self.nodes[op] = node

            if isinstance(op, pf.placeholder):
                value = sources[op.name]
                self.delegate.setEditorData(self, node, value)

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
                    self.editor.addEdge(edge)

            for key, dep in op.kwargs.items():
                isOp = isinstance(dep, pf.Operation)
            
        self.editor.graph.layout()
        self.editor.centerOn(self.editor.graph)

        self.evaluate(sources)


if __name__ == "__main__":
    app = QApplication.instance() or QApplication()
    window = Window(graph, {'a': 90, 'b': 30})
    window.show()
    app.exec_()

