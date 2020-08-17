import pythonflow as pf


class PFSlider(pf.placeholder):
    pass

with pf.Graph() as graph:
    x = PFSlider(name="x")
    y = PFSlider(name="y")
    # z = pf.constant(5, name="z")
    r = (x*y).set_name("r")


from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


import contextlib

from editor.widgets.graphwidget import GraphWidget, GraphWidgetNodeItem, GraphWidgetEdgeItem, GraphWidgetSocketItem


class PFGraphModel(QObject):
    portDataChange = Signal(object) # ((op, key), columnName)
    def __init__(self, pfgraph, result, **sources):
        super().__init__(parent=None)
        assert isinstance(pfgraph, pf.Graph)
        assert set(sources.keys()) == {name for name, op in pfgraph.operations.items() if isinstance(op, pf.placeholder)}

        # data
        self.pfgraph = pfgraph
        self.sources = sources
        self.positions = {} # TODO: implement model based node positions
        self.outputValues = {} # store calculated output values, FIXME: pf keeps the computed values in context, but seems like I cannot access it.
        self._selection = []

    def operations(self):
        return 

from editor import daglib
class GraphView(QWidget):
    portDataChange = Signal(object)
    def __init__(self, pfgraph, **sources):
        super().__init__(parent=None)
        assert isinstance(graph, pf.Graph)
        assert set(sources.keys()) == {name for name, op in graph.operations.items() if isinstance(op, pf.placeholder)}

        # init views
        self.setWindowTitle("pythonflow-editor")
        self.graphWidget = GraphWidget()
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.graphWidget)
        self.graphWidget.scene.selectionChanged.connect(lambda: self.setSelection( {node.op for node in self.graphWidget.scene.selectedItems()} ))

        # noderow: op
        # portrow: op, i or key of args and kwargs
        # edgerow = src portrow and dst portrow

        # map view to model
        self.nodeMap = {} # ModeItem for each operator
        self.edgeMap = {} # EdgeItem for each dependency
        self.socketMap = {} # SocketItem for each portModel
        
        # data
        self.pfgraph = pfgraph
        self.positions = {} # TODO: implement model based node positions
        self.outputValues = {} # store calculated output values, FIXME: pf keeps the computed values in context, but seems like I cannot access it.
        self._selection = []

        # init graph
        self.sources = sources

        self.populateView()

    """ MODEL methods """   
    def setSelection(self, selection):
        assert isinstance(selection, set)
        self._selection = selection
        self.onSelectionChange()                     

    def operations(self):
        """return all node rows """
        for op in graph.operations.values():
            yield op

    def roots(self):
        adj = {}
        for op in self.operations():
            adj[op] = []


        for op in self.operations():
            for dstPort in self.inputPortsForNode(op):
                edge = self.edgeForPort(dstPort)
                if edge is not None:
                    srcPort = self.outputPortForEdge(edge)
                    srcNode = self.nodeForPort(srcPort)
                    adj[op].append(srcNode)

        return daglib.roots(adj)

    def evaluateGraph(self):
        @contextlib.contextmanager
        def syncNode(op, context):
            yield
            port = (op, "DEFAULT")
            value = context[op]
            self.setPortData((port, "value"), value)


        for sink in self.roots():
            res = self.pfgraph(sink, callback=syncNode, **self.sources)

    def portFlags(self, index):
        row, column = index
        op, i = row
        if column is "value":
            if isinstance(op, pf.placeholder) and i is "DEFAULT":
                return Qt.ItemIsEditable
        return Qt.NoItemFlags

    def setSource(self, name, value):
        self.sources[name] = value
        self.evaluateGraph()

    def setPortData(self, index, value, role=Qt.EditRole):
        row, column = index
        if column is "value":
            self.outputValues[row] = value

        op, key = row
        if isinstance(op, pf.placeholder):
            # self.sources[op.name] = value
            # self.setSource(op.name, value)
            self.setSource(op.name, value)
            self.portDataChange.emit(index)
            
            
            # self.evaluateGraph()

        self.portDataChange.emit(index)
        # self.onPortDataChange(index)

    def portData(self, index, role=Qt.DisplayRole):
        if role is Qt.DisplayRole:
            row, column = index
            if column is "name":
                op, key = row
                if key is "DEFAULT":
                    return ""
                else:
                    if isinstance(key, int):
                        return ""
                    else:
                        return str(key)

            if column is "value":
                return str(self.outputValues[row])

        return None

    def inputPortsForNode(self, noderow):
        op = noderow
        for i, dep in enumerate(op.args):
            # if isinstance(dep, pf.Operation):
            yield op, i

        for key, dep in enumerate(op.kwargs):
            yield op, key

    def edgeForPort(self, portrow):
        op, key = portrow
        if isinstance(key, int):
            dep = op.args[key]
        else:
            dep = op.kwargs[key]

        return (dep, "DEFAULT"), (op, key)

    def sourcePortForEdge(self, edgerow):
        dep, srcKey, op, dstKey = edgerow
        return dep, srcKey

    def outputPortsForNode(self, noderow):
        op = noderow
        return [(op, "DEFAULT")]

    def nodeForPort(self, port):
        op, i = port
        return op

    def outputPortForEdge(self, edge):
        return edge[0]

    def inputPortForEdge(self, edge):
        return edge[1]

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
            elif column is "value":
                return "VALUE"
        return None

    """ END: MODEL methods """

    """ DELEGATE methods """
    def createPortEditor(self, index):
        row, column = index
        op, i = row
        if column == "value":
            slider = QGraphicsProxyWidget()
            slider.setWidget(QSlider(Qt.Horizontal))
            slider.widget().valueChanged.connect(lambda value: self.setPortData(index, value))
            slider.widget().setStyleSheet("background: transparent; border: none");
            # slider.widget().valueChanged.connect(lambda value: self.setGraphSource(op.name, value)) # TODO: commitData...with delegate?
            return slider

    def setPortEditorValue(self, editor, index):
        row, column = index
        op, i = row
        editor.widget().setValue(self.sources[op.name])

    """ END: DELEGATE methods"""

    """ VIEW methods """
    def populateView(self):
        # create nodes and ports
        for op in self.operations(): 
            node = GraphWidgetNodeItem(name="{} ({})".format( self.nodeData((op, "name")) , self.nodeData((op, "klass")) ))
            node.op = op

            for port in self.inputPortsForNode(op):
                name = self.portData( (port, "name") )
                socket = GraphWidgetSocketItem(name)
                self.socketMap[port] = socket
                node.addInput(socket)

                flags = self.portFlags( (port, "value") ) 
                if self.portFlags( (port, "value") ) & Qt.ItemIsEditable:
                    editor = self.createPortEditor( (port, "value") )

                    node._outputs[0].layout().insertItem(0, editor)
                    self.setPortEditorValue( (port, "value"), self.sources[op.name] )

            for port in self.outputPortsForNode(op):
                name = self.portData( (port, "name") )
                socket = GraphWidgetSocketItem(name)
                self.socketMap[port] = socket
                node.addOutput(socket)

                flags = self.portFlags( (port, "value") ) 
                if self.portFlags( (port, "value") ) & Qt.ItemIsEditable:
                    editor = self.createPortEditor( (port, "value") )
                    node._outputs[0].layout().insertItem(0, editor)
                    self.setPortEditorValue( editor, (port, "value"))

            # add node to the window
            self.graphWidget.addNode(node)
            self.nodeMap[op] = node

        # create edges
        for op in graph.operations.values():
            for inputPort in self.inputPortsForNode(op):
                edge = self.edgeForPort(inputPort)
                outputPort = self.outputPortForEdge(edge)
                outputItem = self.socketMap[outputPort]
                inputItem = self.socketMap[self.inputPortForEdge(edge)]

                edgeItem = GraphWidgetEdgeItem(outputItem, inputItem)
                self.graphWidget.addEdge(edgeItem)

            for key, dep in op.kwargs.items():
                isOp = isinstance(dep, pf.Operation)
            
        self.graphWidget.graph.layout()
        self.graphWidget.centerOn(self.graphWidget.graph)

        self.portDataChange.connect(self.onPortDataChange)
        self.evaluateGraph()

    def onSelectionChange(self):
        # sync graph widget selection
        oldState = self.graphWidget.scene.blockSignals(True)
        for op, node in self.nodeMap.items():
            isOpSelected = id(op) in {id(_) for _ in self._selection}
            isNodeSelected = node.isSelected()
            if isOpSelected != isNodeSelected:
                node.setSelected(isOpSelected)

        self.graphWidget.scene.blockSignals(oldState)

    def onPortDataChange(self, index):
        """ update port view """
        row, column = index
        op, i = row
        if column is "value":
            socket = self.socketMap[row]
            socket.setText(self.portData(index))

    """ END: VIEW methods """


if __name__ == "__main__":
    app = QApplication.instance() or QApplication()
    window = GraphView(graph, **{'x': 90, 'y': 30})
    window.show()
    app.exec_()

