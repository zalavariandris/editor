from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
import sys

class Viewer2D(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy ( Qt.ScrollBarAlwaysOff )
        self.setVerticalScrollBarPolicy ( Qt.ScrollBarAlwaysOff )
        self.setTransformationAnchor(QGraphicsView.NoAnchor);

        for gesture in [Qt.TapGesture, Qt.TapAndHoldGesture, Qt.PinchGesture, Qt.PanGesture,  Qt.SwipeGesture, Qt.CustomGesture]:
            self.grabGesture(gesture)

        # crate temporary scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setSceneRect(-sys.maxsize/4, -sys.maxsize/4, sys.maxsize/2, sys.maxsize/2) # x, y, w, h

        self.setBackgroundBrush(QBrush(QColor(240, 240, 240), Qt.SolidPattern))

        self.drawAxis = True
        self.drawGrid = True

        self.setMouseTracking(True)

    def panView(self, dx, dy):
        sceneDelta = self.mapToScene(QPoint(dx, dy)) - self.mapToScene(0,0)
        self.translate(sceneDelta.x(), sceneDelta.y())

    def zoomView(self, zoom, anchor=QPointF()):
        oldCenterPoint = self.mapToScene(anchor)
        self.scale(zoom, zoom)
        newCenterPoint = self.mapToScene(anchor)
        delta = newCenterPoint - oldCenterPoint
        self.translate(delta.x(), delta.y())

    def rotateView(self, angle, anchor=QPointF()):
        oldCenterPoint = self.mapToScene(anchor)
        self.rotate(angle)
        newCenterPoint = self.mapToScene(anchor)
        delta = newCenterPoint - oldCenterPoint
        self.translate(delta.x(), delta.y())

    def mousePressEvent(self, event):
        self.lastMousePos = event.pos()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if event.modifiers() == Qt.AltModifier:
                delta = event.pos() - self.lastMousePos
                self.panView(delta.x(), delta.y())
        if event.buttons() == Qt.MiddleButton:
            if event.modifiers() == Qt.NoModifier:
                delta = event.pos() - self.lastMousePos
                self.panView(delta.x(), delta.y())
        self.lastMousePos = event.pos()
        return super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        zoomSpeed = 0.001
        delta = event.angleDelta().y() # consider implementing pixelDelta for macs
        zoomFactor = (1+delta*zoomSpeed)

        self.zoomView(zoomFactor, anchor=event.pos())

    def event(self, event):
        if event.type() == QEvent.Gesture:
            return self.gestureEvent(event)
        return super().event(event)

    def gestureEvent(self, event):
        swipe = event.gesture(Qt.SwipeGesture)
        pan = event.gesture(Qt.PanGesture)
        pinch = event.gesture(Qt.PinchGesture)

        if swipe:
            self.swipeTriggered(swipe)

        if pan:
            self.panTriggered(pan)

        if pinch:
            self.pinchTriggered(pinch)

        return True

    def swipeTriggered(self, event):
        pass

    def panTriggered(self, event):
        pass

    def pinchTriggered(self, pinch):
        changeFlags = pinch.changeFlags()
        if changeFlags & QPinchGesture.ScaleFactorChanged:
            anchor = self.mapFromGlobal(pinch.centerPoint().toPoint())
            self.zoomView(pinch.scaleFactor(), anchor)

        if changeFlags & QPinchGesture.CenterPointChanged:
            moved = (pinch.centerPoint()-pinch.lastCenterPoint())
            self.panView(moved.x(), moved.y())
            
        if changeFlags & QPinchGesture.RotationAngleChanged:
            anchor = self.mapFromGlobal(pinch.centerPoint().toPoint())
            self.rotateView(pinch.rotationAngle() - pinch.lastRotationAngle(), anchor)

        return True

    def drawForeground(self, painter, rect):
        """Draw axis"""
        if self.drawAxis:
            painter.setPen(QPen(QColor(255,0,0), 0))
            painter.drawLine(0,0,100,0)
            painter.setPen(QPen(QColor(0,255,0), 0))
            painter.drawLine(0,0,0,100)

    @property
    def zoom(self):
        x_scale = QVector2D(self.transform().m11(), self.transform().m21()).length()
        y_scale = QVector2D(self.transform().m12(), self.transform().m22()).length()
        return x_scale

    def drawBackground(self, painter, rect):
        """ Draw background pattern """
        super().drawBackground(painter, rect)

        """ Draw grid """
        if self.drawGrid:
            import math
            zoomfactor = self.zoom
            gridSize = 300 * math.pow(10, math.floor(math.log(1/zoomfactor, 10)))
            gridSize = gridSize


            left = rect.left() - rect.left() % gridSize
            top = rect.top() - rect.top() % gridSize
     
            lines = []
     
            x = left
            while x<rect.right():
                x+=gridSize
                lines.append(QLineF(x, rect.top(), x, rect.bottom()))

            y = top
            while y<rect.bottom():
                y+=gridSize
                lines.append(QLineF(rect.left(), y, rect.right(), y))
     

            painter.setPen(QPen(QBrush(QColor(128,128,128, 56)), 0))
            painter.drawLines(lines)

    def bringToFront(self, item):
        self.scene.removeItem(item)
        self.scene.addItem(item)

class Viewer(QWidget):
    selectionChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(10,10,10,10)
        self.body = Viewer2D()
        self.body.scene.selectionChanged.connect(self.selectionChanged.emit)
        self.layout().addWidget(self.body)

    def addItem(self, item):
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.body.scene.addItem(item)

    def selection(self):
        return self.body.scene.selectedItems()

if __name__ == "__main__":
    import sys, os
    app = QApplication(sys.argv)
    viewer = Viewer()
    viewer.show()
    viewer.addItem(QGraphicsRectItem(0,0,200,200))
    def on_selection_changed():
        print("selection changed", viewer.selection())
        
    viewer.selectionChanged.connect(on_selection_changed)
    app.exec_()
    os._exit(0)
