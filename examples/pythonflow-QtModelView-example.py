import pythonflow as pf



def migthBeUUID(text: str)->bool:
    if len(text)!=32:
        return False

    return all(s in "0123456789abcdef" for s in text)
    

class PFSlider(pf.placeholder):
    pass


DEFAULT_OUTPUT = ""

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from editor import daglib
import contextlib
from editor.widgets.graphwidget import GraphWidget, GraphWidgetNodeItem, GraphWidgetEdgeItem, GraphWidgetSocketItem


class PFGraphModel(QObject):
    portDataChange = Signal(object)
    nodeSelectionChange = Signal()
    def __init__(self, pfgraph, **sources):
        super().__init__(parent=None)
        assert isinstance(pfgraph, pf.Graph)
        assert set(sources.keys()) == {name for name, op in pfgraph.operations.items() if isinstance(op, pf.placeholder)}

        # noderow: op
        # portrow: op, i or key of args and kwargs
        # edgerow = src portrow and dst portrow
        
        # data
        self.pfgraph = pfgraph
        self.positions = {} # TODO: implement model based node positions
        self.outputValues = {} # store calculated output values, FIXME: pf keeps the computed values in context, but seems like I cannot access it.
        self._nodeSelection = []

        # init graph
        self.sources = sources

        self._evaluateGraph()
 
    def setNodeSelection(self, selection):
        assert isinstance(selection, set)
        self._nodeSelection = selection
        self.nodeSelectionChange.emit()        

    def nodeSelection(self):
        return self._nodeSelection        

    def _rootNodes(self):
        adj = {}
        for op in self.nodes():
            adj[op] = []


        for op in self.nodes():
            for dstPort in self.nodeInputs(op):
                edge = self.portEdge(dstPort)
                if edge is not None:
                    srcPort = self.edgeTarget(edge)
                    srcNode = self.portNode(srcPort)
                    adj[op].append(srcNode)

        return daglib.startNodes(adj)

    def _evaluateGraph(self):
        @contextlib.contextmanager
        def onNodeEvaluate(op, context):
            yield
            # get node output value
            value = context[op]

            # get output port
            port = (op, DEFAULT_OUTPUT)

            # store output value
            self.outputValues[port] = value

            # emit port data change
            self.portDataChange.emit( (port, "value") )

        for sink in self._rootNodes():
            res = self.pfgraph(sink, callback=onNodeEvaluate, **self.sources)

    """Data"""
    def portData(self, index, role=Qt.DisplayRole):
        row, column = index
        op, key = row
        if column is "value":
            if isinstance(op, pf.placeholder):
                value = self.sources[op.name]
            else:
                value = self.outputValues.get(row, None)

            if role is Qt.EditRole:
                return value
            elif role is Qt.DisplayRole:
                return str(value)
        elif column is "name":
            return str(key)

        raise NotImplementedError

    def edgeData(self, index, role=Qt.DisplayRole):
        edge, column = index
        if column is "name":
            port = self.edgeSource(edge)
            return self.portData( (port, "name") )
        else:
            raise NotImplementedError

    def setPortData(self, index, value, role=Qt.EditRole):
        row, column = index
        op, key = row
        if column is "value":   
            if isinstance(op, pf.placeholder):
                self.sources[op.name] = value
                self._evaluateGraph()
            else:
                self.outputValues[row] = value

        self.portDataChange.emit(index)

    def portFlags(self, index):
        row, column = index
        op, i = row
        if column is "value":
            if isinstance(op, pf.placeholder) and i is DEFAULT_OUTPUT:
                value = self.portData(index, role=Qt.EditRole)
                if isinstance(value, float):
                    return Qt.ItemIsEditable
                if isinstance(value, int):
                    return Qt.ItemIsEditable
                if isinstance(value, str):
                    return Qt.ItemIsEditable
        return Qt.NoItemFlags
    
    def nodeData(self, index, role=Qt.DisplayRole):
        op, column = index
        if role is Qt.DisplayRole:
            if column is "name":
                if migthBeUUID(op.name):
                    return None
                else:
                    return op.name
            elif column is "klass":
                if type(op)==pf.operations.func_op:
                    return op.target.__name__
                else:
                    return str( op.__class__.__name__ )
            elif column is "value":
                return "VALUE"
        return None

    """ Relations """
    def nodes(self):
        """return all node rows """
        for op in self.pfgraph.operations.values():
            yield op

    def nodeInputs(self, noderow):
        op = noderow
        for i, dep in enumerate(op.args):
            if isinstance(dep, pf.Operation):
                yield op, i

        for key, dep in op.kwargs.items():
            if isinstance(dep, pf.Operation):
                yield op, key

    def nodeOutputs(self, noderow):
        op = noderow
        return [(op, DEFAULT_OUTPUT)]

    def portNode(self, port):
        op, i = port
        return op

    def portEdge(self, portrow):
        op, key = portrow
        if isinstance(key, int):
            dep = op.args[key]
        else:
            dep = op.kwargs[key]

        return (dep, DEFAULT_OUTPUT), (op, key)

    def edgeTarget(self, edge):
        return edge[0]

    def edgeSource(self, edge):
        return edge[1]


class GraphView(QWidget):
    commitPortData = Signal(object)
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.model = None

        # init views
        self.setWindowTitle("pythonflow-editor")
        self.graphWidget = GraphWidget()
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.graphWidget)

        # map view to model
        self.nodeMap = {} # ModeItem for each operator
        self.edgeMap = {} # EdgeItem for each dependency
        self.socketMap = {} # SocketItem for each portModel
        self.socketEditors = {}

    def setModel(self, model):
        self.model = model
        self.graphWidget.scene.selectionChanged.connect(lambda: self.model.setNodeSelection( {node.op for node in self.graphWidget.scene.selectedItems()} ))
        self.model.nodeSelectionChange.connect(self._onSelectionChange)
        self._populateView()

        self.commitPortData.connect(self.onPortEditorCommitData)

    def _populateView(self):
        # create nodes and portss
        for op in self.model.nodes():
            name = self.model.nodeData( (op, "name") )
            klass = self.model.nodeData( (op, "klass") )
            if isinstance(op, pf.placeholder):
                title = "<p><i>{}</i></p>".format(name)
            else:
                if name is not None:
                    title = "<p><b>{}</b></p><p><i>{}</i></p>".format( klass, name )
                else:
                    title = "<p><b>{}</b></p>".format(klass)
            
            node = GraphWidgetNodeItem(
                title=title,
                collapsed=True
                )
            node.op = op

            for port in self.model.nodeInputs(op):
                name = self.model.portData( (port, "name") )
                socket = GraphWidgetSocketItem(name)
                self.socketMap[port] = socket
                node.addInput(socket)

                flags = self.model.portFlags( (port, "value") ) 
                if self.model.portFlags( (port, "value") ) & Qt.ItemIsEditable:
                    editor = self.createPortEditor( (port, "value") )
                    editor.index = (port, "value")
                    proxyWidget = QGraphicsProxyWidget()
                    proxyWidget.setWidget(editor)
                    node._outputs[0].layout().insertItem(0, proxyWidget)
                    self.setPortEditorData( (port, "value"), self.model, (port, "value") )

                self._patchPortData( (port, "name") )
                self._patchPortData( (port, "value") )

            for port in self.model.nodeOutputs(op):
                name = self.model.portData( (port, "name") )
                socket = GraphWidgetSocketItem(name)
                self.socketMap[port] = socket
                node.addOutput(socket)

                flags = self.model.portFlags( (port, "value") )
                if flags & Qt.ItemIsEditable:
                    editor = self.createPortEditor( (port, "value") )
                    editor.index = (port, "value")
                    proxyWidget = QGraphicsProxyWidget()
                    proxyWidget.setWidget(editor)
                    node._outputs[0].layout().insertItem(0, proxyWidget)
                    self.setPortEditorData( editor, self.model, (port, "value"))

                self._patchPortData( (port, "name") )
                self._patchPortData( (port, "value") )

            # add node to the window
            self.graphWidget.addNode(node)
            self.nodeMap[op] = node

        # create edges
        for op in self.model.nodes():
            for inputPort in self.model.nodeInputs(op):
                edge = self.model.portEdge(inputPort)
                outputPort = self.model.edgeTarget(edge)
                outputItem = self.socketMap[outputPort]
                inputItem = self.socketMap[self.model.edgeSource(edge)]

                edgeItem = GraphWidgetEdgeItem(outputItem, inputItem)
                name = self.model.edgeData( (edge, "name") )
                edgeItem.setText(name)
                self.graphWidget.addEdge(edgeItem)

            for key, dep in op.kwargs.items():
                isOp = isinstance(dep, pf.Operation)
            
        self.graphWidget.graph.layout()
        self.graphWidget.centerOn(self.graphWidget.graph)

        self.model.portDataChange.connect(self._patchPortData)
        
    def _onSelectionChange(self):
        # sync graph widget node selection
        oldState = self.graphWidget.scene.blockSignals(True)
        for op, node in self.nodeMap.items():
            isOpSelected = id(op) in {id(_) for _ in self.model.nodeSelection()}
            isNodeSelected = node.isSelected()
            if isOpSelected != isNodeSelected:
                node.setSelected(isOpSelected)

        self.graphWidget.scene.blockSignals(oldState)

    def _patchPortData(self, index):
        """ update port view """
        row, column = index
        op, i = row
        if column is "name" or "value":
            socket = self.socketMap[row]
            nameText = self.model.portData((row, "name"))
            valueText = self.model.portData( (row, "value") )
            if self.model.portData( (row, "value"), Qt.EditRole ) is not None:
                socket.setText("{}({})".format(nameText, valueText))
            else:
                socket.setText(nameText)

    # delegation methods
    def createPortEditor(self, index)->QWidget:
        row, column = index
        op, i = row
        if column == "value":
            value = self.model.portData(index, role=Qt.EditRole)
            # FIXME: return widget instead of QGraphicsItem
            if isinstance(value, int):
                editor = QSlider(Qt.Horizontal)
                editor.valueChanged.connect(lambda: self.commitPortData.emit(editor))
                # editor.setStyleSheet("background: transparent; border: none");
                editor.setMinimumSize(100, 0)
                return editor

            if isinstance(value, float):
                editor = QSlider(Qt.Horizontal)
                editor.valueChanged.connect(lambda: self.commitPortData.emit(editor))
                # editor.setStyleSheet("background: transparent; border: none");
                return editor

            if isinstance(value, str):
                editor = QLineEdit()
                editor.textEdited.connect(lambda: self.commitPortData.emit(editor))
                return editor

        raise NotImplementedError("editable flag shoud return Not editble for index:", index)

    def onPortEditorCommitData(self, editor:QWidget)->None:
        index = editor.index
        self.setPortModelData(editor, self.model, index)

    def setPortEditorData(self, editor:QWidget, model, index)->None:
        """Sets the contents of the given editor to the data for the item at the given index."""
        row, column = index
        op, i = row
        value = self.model.portData(index, Qt.EditRole)
        if isinstance(value, int):
            editor.setValue(model.portData(index, role=Qt.EditRole))
        if isinstance(value, float):
            editor.widget().setValue(model.portData(index, role=Qt.EditRole))
        if isinstance(value, str):
            lineEdit = QLineEdit()
            editor.setText(model.portData(index, role=Qt.EditRole))

    def setPortModelData(self, editor:QWidget, model, index)->None:
        """Sets the data for the item at the given index in the model to the contents of the given editor."""
        value = self.model.portData(index, Qt.EditRole)
        if isinstance(value, int):
            model.setPortData(index, editor.value())
        if isinstance(value, float):
            model.setPortData(index, editor.value())
        if isinstance(value, str):
            model.setPortData(index, editor.text())


import numpy as np
class GraphicsRenderer(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self._input = None

    def setInput(self, value):
        self._input = value
        self.prepareGeometryChange()

    def input(self):
        return self._input

    def paint(self, painter, option, widget):
        if isinstance(self._input, QPainterPath):
            painter.drawPath(self._input)
        elif isinstance(self._input, QImage):
            pianter.drawImage(0,0, self.input)
        elif isinstance(self._input, QPixmap):
            painter.drawPixmap(0,0,self.input)
        elif isinstance(self._input, (np.ndarray, np.generic)) and len(self._input.shape) == 3:
            cvImg = self._input
            height, width, channels = cvImg.shape
            bytesPerLine = 3 * width
            qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_RGB888)
            # pixmap = QtGui.QPixmap.fromImage(image.copy())
            painter.drawImage(0,0,qImg)
        else:
            painter.drawText( 0,0, str(self._input) )

    def boundingRect(self):
        if isinstance(self.input, QPainterPath):
            return self._input.boundingRect()
        elif isinstance(self.input, QImage):
            return self.input.rect()
        elif isinstance(self.input, QPixmap):
            return self.input.rect()
        elif isinstance(self._input, (np.ndarray, np.generic)) and len(self._input.shape) == 3:
            height, width, channels = self._input.shape
            return QRect(0,0, width, height)
        else:
            font = QApplication.font()
            fm =  QFontMetrics(font)
            return fm.boundingRect(str(self._input))

from editor.widgets.viewer2D import Viewer
from editor.read import read

readop = pf.opmethod(read)

class Window(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # create pfgraph
        with pf.Graph() as graph:
            imageio = pf.import_('imageio')
            ndimage = pf.import_('scipy.ndimage')
            np = pf.import_('numpy')

            x = PFSlider(name="x")
            y = PFSlider(name="y")
            r = (x*y).set_name("r")

            frame = pf.placeholder("frame")
            readop(path=pf.placeholder('filepath'), frame=frame)
            # image = imageio.imread(filename).set_name('imread')

        self.setLayout(QHBoxLayout())

        self.model = PFGraphModel(graph, **{'x': 90, 'y': 30, 'frame':0, 'filepath': "C:/Users/andris/Videos/M2U00001.MPG"})
        self.graphview = GraphView()
        self.graphview.setModel(self.model)
        self.viewer = Viewer()
        self.layout().addWidget(self.graphview)
        self.layout().addWidget(self.viewer)

        self.renderer = GraphicsRenderer()
        self.viewer.addItem(self.renderer)
        self.viewer.body.centerOn(0,0)

        def onSelectionChange():
            """show output results in viewer"""
            if len(self.model.nodeSelection())>0:
                for node in self.model.nodeSelection():
                    outputPorts = self.model.nodeOutputs(node)
                    port = outputPorts[0]
                    outputValue = self.model.portData( (port, "value"), Qt.EditRole )
                    self.renderer.setInput(outputValue)
                    self.renderer.update()
            else:
                self.renderer.setInput(None)
                self.renderer.update()

        def onDataChange(index):
            for node in self.model.nodeSelection():
                outputPorts = self.model.nodeOutputs(node)
                port = outputPorts[0]
                outputValue = self.model.portData( (port, "value"), Qt.EditRole )
                self.renderer.setInput(outputValue)
                self.renderer.update()

        self.model.nodeSelectionChange.connect(onSelectionChange)
        self.model.portDataChange.connect(onDataChange)

if __name__ == "__main__":
    app = QApplication.instance() or QApplication()
    
    window = Window()
    # view = GraphView()
    # view.setModel(model)
    
    window.show()
    app.exec_()

