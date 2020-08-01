from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from editor.widgets.viewer2D import Viewer2D
from editor import daglib

def findIntersection(A:QLineF, B:QLineF)->QPointF:
    x1 = A.p1().x()
    y1 = A.p1().y()
    x2 = A.p2().x()
    y2 = A.p2().y()

    x3 = B.p1().x()
    y3 = B.p1().y()
    x4 = B.p2().x()
    y4 = B.p2().y()

    px=( (x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4) ) / ( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) ) 
    py=( (x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4) ) / ( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) )
    point = QPointF(px, py)

    bbox1 = QRectF(A.p1(), A.p2()).normalized()
    bbox2 = QRectF(B.p1(), B.p2()).normalized()

    bbox = bbox1.united(bbox2)

    if bbox2.adjusted(-1,-1,1,1).contains(point) and bbox1.adjusted(-1,-1,1,1).contains(point):
        return point
    else:
        return None

def intersect(line:QLineF, rect:QRectF)->QPointF:
    top =  QLineF(rect.topLeft(), rect.topRight())
    left = QLineF(rect.topLeft(), rect.bottomLeft())
    right = QLineF(rect.topRight(), rect.bottomRight())
    bottom = QLineF(rect.bottomLeft(), rect.bottomRight())

    for side in [top, left, right, bottom]:
        intersection = findIntersection(line, side)
        if intersection is not None:
            return intersection

    return None


class Pin(QGraphicsLayoutItem):
    def __init__(self):
        super().__init__()
        self.ellipse = QGraphicsEllipseItem(0,0,12,12)
        self.setGraphicsItem(self.ellipse)

    def sizeHint(self , which, constraint):
        # return QSize(5,5)
        return self.ellipse.rect().size()

    def setGeometry(self, rect):
        self.ellipse.setPos(rect.topLeft())


class SocketBase(QGraphicsWidget):
    def __init__(self):
        super().__init__()
        self.edge = None
        self.node = None


class GraphWidgetSocketItem(SocketBase):
    def __init__(self, text, alignment="Left"):
        super().__init__()
        self.setLayout(QGraphicsLinearLayout())

        label = QGraphicsProxyWidget()
        label.setWidget(QLabel(text))
        label.widget().setAlignment(Qt.AlignLeft if alignment == "Left" else Qt.AlignRight)
       
        pin = Pin()
        self.pin = pin


        self.label = label
        # label.widget().setAlignment(Qt.AlignRight)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addItem(label)
        self.layout().addItem(pin)
        self.setText(text)
        self.setAlignment(alignment)
        self.setFont(QApplication.font())
        self.diameter = 12
        self.spacing = 3

    def setFont(self, font):
        self._font = font

    def font(self):
        return self._font

    def setText(self, text):
        self.label.widget().setText(text)
        fm = QFontMetrics(self.label.widget().font())
        self.label.widget().setMinimumSize(fm.width(text), 10)
        # self.label.widget().updateGeometry()

    def text(self):
        return self._text

    def setAlignment(self, alignment):
        if alignment == "Left":
            self.layout().removeItem(self.pin)
            self.layout().insertItem(0, self.pin)

        if alignment == "Right":
            self.layout().removeItem(self.pin)
            self.layout().addItem(self.pin)

        self.label.widget().setAlignment(Qt.AlignLeft if alignment == "Left" else Qt.AlignRight)


    def pinPos(self):
        return self.pin.graphicsItem().mapToScene( self.pin.graphicsItem().boundingRect().center() )

class NodeBase():
    def __init__(self):
        self.graph = None
        self._inputs = []
        self._outputs = []

class GraphWidgetNodeItem(NodeBase, QGraphicsWidget):
    def __init__(self, name):
        NodeBase.__init__(self)
        QGraphicsWidget.__init__(self)

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        self.setLayout(QGraphicsLinearLayout(Qt.Vertical))
        self.layout().setSpacing(5)
        self.layout().setContentsMargins(11,11,11,11)

        # header
        header = QGraphicsWidget()
        # header.setAutoFillBackground(True)
        title = QGraphicsTextItem(name)
        header.setMinimumSize(QFontMetrics(title.font()).size(Qt.TextSingleLine, title.toPlainText()))
        header.setPreferredSize(QFontMetrics(title.font()).size(Qt.TextSingleLine, title.toPlainText()))

        header.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        title.setParentItem(header)
        title.setPos(-4,-5)
        
        # body
        body = QGraphicsWidget()
        body.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        body.setLayout(QGraphicsLinearLayout(Qt.Horizontal))
        body.layout().setSpacing(11)
        body.layout().setContentsMargins(0,0,0,0)

        inputArea = QGraphicsWidget()
        # inputArea.setAutoFillBackground(True)
        inputArea.setLayout(QGraphicsLinearLayout(Qt.Vertical))
        inputArea.layout().setContentsMargins(0,0,0,0)
        inputArea.layout().setSpacing(3)
        inputArea.layout().addStretch()
        
        outputArea = QGraphicsWidget()
        # outputArea.setAutoFillBackground(True)
        palette = outputArea.palette()
        palette.setBrush(QPalette.Window, QColor(0,0,0,10))
        outputArea.setPalette(palette)
        outputArea.setLayout(QGraphicsLinearLayout(Qt.Vertical))
        outputArea.layout().setContentsMargins(0,0,0,0)
        outputArea.layout().setSpacing(3)
        outputArea.layout().addStretch()
        
        body.layout().addItem(inputArea)
        body.layout().addItem(outputArea)

        self.inputArea = inputArea
        self.outputArea = outputArea
        self._collapsed = False

        # footer
        footer = QGraphicsWidget()
        footer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        # footer.setAutoFillBackground(True)
        status = QGraphicsTextItem("-status-")
        footer.setMinimumSize(QFontMetrics(status.font()).size(Qt.TextSingleLine, status.toPlainText()))
        status.setParentItem(footer)

        self.body = body
        self.header = header
        self.layout().addItem(self.header)
        self.layout().addItem(self.body)
        # self.layout().addItem(footer)

    def collapse(self):
        body = self.layout().itemAt(1)
        self.layout().removeAt(1)
        self.scene().removeItem(body)
        self.layout().activate()
        self._collapsed = True

        for socket in self._inputs+self._outputs:
            if socket.edge is not None:
                socket.edge.updatePosition()

    def expand(self):
        print("expand")
        self.layout().insertItem(1,self.body)
        self.layout().activate()
        self._collapsed = False

        for socket in self._inputs+self._outputs:
            if socket.edge is not None:
                socket.edge.updatePosition()

    def isCollapsed(self):
        return self._collapsed

    def paint(self, painter, option, widget):
        frame = QRectF( QPointF(0,0), self.geometry().size() )
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255,255,255,200))
        painter.drawRoundedRect(frame.adjusted(5,5,-5,-5), 3, 3)

        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(frame, 3, 3)

    def addInput(self, socket):
        socket.setAlignment("Left")
        socket.node = self
        self.inputArea.layout().insertItem(self.inputArea.layout().count(), socket)
        self._inputs.append(socket)

    def addOutput(self, socket):
        socket.setAlignment("Right")
        socket.node = self
        self.outputArea.layout().insertItem(self.outputArea.layout().count(), socket)
        self._outputs.append(socket)

    def itemChange(self, change, value):
        if change is QGraphicsItem.ItemPositionHasChanged:
            if self.graph is not None:
                self.graph.prepareGeometryChange()
            for socket in self._inputs+self._outputs:
                if socket.edge is not None:
                    socket.edge.updatePosition()

        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        if self.isCollapsed():
            self.expand()
        else:
            self.collapse()

    def __repr__(self):
        return "Node({})".format(self.layout().itemAt(0).childItems()[0].toPlainText())

import math
class EdgeBase:
    def __init__(self, outputPin, inputPin):
        self.outputPin = outputPin
        self.inputPin = inputPin
        inputPin.edge = self
        outputPin.edge = self
        self.graph = None

class GraphWidgetEdgeItem(EdgeBase, QGraphicsItemGroup):
    def __init__(self, outputPin, inputPin):
        EdgeBase.__init__(self, outputPin, inputPin)
        QGraphicsItemGroup.__init__(self)
        # super().__init__()
        # self.graph = None
        # self.outputPin = outputPin
        # self.inputPin = inputPin
        # outputPin.edge = self
        # inputPin.edge = self

        self.body = QGraphicsLineItem()
        self.body.setParentItem(self)
        self.body.setPen(QPen(Qt.black, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.head = QGraphicsPolygonItem()
        self.head.setParentItem(self)
        self.head.setBrush(Qt.black)
        self.head.setPen(QPen(Qt.black, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.head.setPolygon(QPolygonF([QPointF(0,0), QPointF(10,-6), QPointF(10, 6)]))

        self.updatePosition()

    def updatePosition(self):
        if self.outputPin.node.isCollapsed():
            sourcePos = self.outputPin.node.geometry().center()
        else:
            sourcePos = self.outputPin.pinPos()

        if self.inputPin.node.isCollapsed():
            targetPos = self.inputPin.node.geometry().center()
        else:
            targetPos = self.inputPin.pinPos()

        if self.outputPin.node.isCollapsed():
            intersection = intersect(QLineF(sourcePos, targetPos), self.outputPin.node.geometry().adjusted(-3,-3,3,3))
            sourcePos = intersection

        if self.inputPin.node.isCollapsed():
            intersection = intersect(QLineF(sourcePos, targetPos), self.inputPin.node.geometry().adjusted(-3,-3,3,3))
            targetPos = intersection

        self.body.setLine(QLineF(sourcePos, targetPos))

        angle = math.atan2(sourcePos.y()- targetPos.y(), sourcePos.x()-targetPos.x())
        self.head.setPos(targetPos)
        self.head.setRotation(angle/math.pi*180)


class Graph(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.edges = []

    def addNode(self, node):
        node.setParentItem(self)
        node.graph = self
        self.nodes.append(node)

    def addEdge(self, edge):
        edge.setParentItem(self)
        edge.graph = self
        self.edges.append(edge)

    def paint(self, painter, option, widget):
        return
        painter.drawRoundedRect(self.childrenBoundingRect().adjusted(-3,-3,3,3), 3, 3)

    def boundingRect(self):
        return self.childrenBoundingRect().adjusted(-10,-10,10,10)

    def layout(self):
        nodes = [node for node in self.nodes]
        adj = dict([(node, [socket.edge.outputPin.node for socket in node._inputs if socket.edge]) for node in nodes])

        
        positions = daglib.layout(adj)

        for node, (x,y) in positions:
            node.setPos(-y*200, x*200)


class GraphWidget(Viewer2D):
    def __init__(self):
        super().__init__()
        self.graph = Graph()
        self.scene.addItem(self.graph)
        # self.drawGrid = False
        self.setWindowTitle("GraphWidget")
        # self.setViewport(QOpenGLWidget() )

    def addNode(self, node):
        self.graph.addNode(node)

    def addEdge(self, edge):
        self.graph.addEdge(edge)


if __name__ == "__main__":
    app = QApplication()
    graphWidget = GraphWidget()

    # create nodes
    tpsNode = GraphWidgetNodeItem("ThinPlateSpline")
    tpsNode.setPos(600, 250)
    tpsNode.addInput(GraphWidgetSocketItem("image"))
    tpsNode.addInput(GraphWidgetSocketItem("sourcePath"))
    tpsNode.addInput(GraphWidgetSocketItem("targetPath"))
    tpsNode.addOutput(GraphWidgetSocketItem("deformed"))
    graphWidget.addNode(tpsNode)

    readNode = GraphWidgetNodeItem("Read")
    readNode.setPos(300,100)
    readNode.addInput(GraphWidgetSocketItem("file"))
    readNode.addInput(GraphWidgetSocketItem("frame"))
    readNode.addOutput(GraphWidgetSocketItem("image"))
    graphWidget.addNode(readNode)

    srcPathNode = GraphWidgetNodeItem("SourcePath")
    srcPathNode.setPos(300,300)
    srcPathNode.addOutput(GraphWidgetSocketItem("path"))
    graphWidget.addNode(srcPathNode)

    tgtPathNode = GraphWidgetNodeItem("TargetPath")
    tgtPathNode.setPos(300,500)
    tgtPathNode.addOutput(GraphWidgetSocketItem("path"))
    graphWidget.addNode(tgtPathNode)

    # create edges
    edge = GraphWidgetEdgeItem(readNode._outputs[0], tpsNode._inputs[0])
    edge.setZValue(-1)
    graphWidget.addEdge(edge)
    edge = GraphWidgetEdgeItem(srcPathNode._outputs[0], tpsNode._inputs[1])
    edge.setZValue(-1)
    graphWidget.addEdge(edge)
    edge = GraphWidgetEdgeItem(tgtPathNode._outputs[0], tpsNode._inputs[2])
    edge.setZValue(-1)
    graphWidget.addEdge(edge)

    graphWidget.show()

    graphWidget.graph.layout()
    graphWidget.centerOn(graphWidget.graph)
    app.exec_()
