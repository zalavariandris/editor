from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class PathEditor(QObject, QGraphicsPathItem):
    pathChanged = Signal()

    def __init__(self):
        QObject.__init__(self)
        QGraphicsPathItem.__init__(self)
        
        self.controls = []
        self.tangents = []
        # self.createControlPoints()
        self.setPen(QPen(QColor("darkorange"), 0))

    def setPath(self, path):
        super().setPath(path)
        self.patchControls()
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged:
            self.onSceneHasChanged()

        return super().itemChange(change, value)

    def onSceneHasChanged(self):
        if self.scene() is not None:
            self.patchControls()
        else:
            self.destroyControls()
        
    def patchControls(self):
        path = self.path()
        elementsCount = path.elementCount()
        ctrlsCount = len(self.controls)

        # add missing control points
        for i in range( ctrlsCount, elementsCount ):
            element = path.elementAt(i)

            # ctrlPoint
            ctrlPoint = QGraphicsEllipseItem(-5,-5,10,10)
            ctrlPoint.setParentItem(self)
            ctrlPoint.installSceneEventFilter(self)
            ctrlPoint.setBrush(QColor("darkorange"))
            ctrlPoint.setPen(Qt.NoPen)
            # ctrlPoint.setFlag(QGraphicsItem.ItemIsSelectable, True)
            # ctrlPoint.setFlag(QGraphicsItem.ItemIsMovable, True)
            # ctrlPoint.setFlag(QGraphicsItem.ItemSendsGeometryChanges , True)
            ctrlPoint.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)

            # ctrlPoint.setAcceptHoverEvents(True)
            ctrlPoint.userData = i
            self.controls.append(ctrlPoint)

            # outTangent
            if i<elementsCount:
                nextElement = path.elementAt(i+1)
                if nextElement.type is QPainterPath.ElementType.CurveToElement:
                    outTangent = QGraphicsLineItem()
                    outTangent.setPen(QPen(QBrush(QColor("darkorange")), 0, Qt.DashLine))
                    outTangent.setParentItem(self)
                    ctrlPoint.outTangent = outTangent

            # inTangent
            if i>0:
                prevElement = path.elementAt(i-1)
                if element.type is QPainterPath.ElementType.CurveToDataElement and prevElement.type is QPainterPath.ElementType.CurveToDataElement:
                    inTangent = QGraphicsLineItem()
                    inTangent.setPen(QPen(QBrush(QColor("darkorange")), 0, Qt.DashLine))
                    inTangent.setParentItem(self)
                    ctrlPoint.inTangent = inTangent

        # remove additional control points
        for i in range( elementsCount, ctrlsCount ):
            raise NotImplementedError

        # update control points
        for i, control in enumerate(self.controls):
            element = path.elementAt(i)
            control.setPos(element.x, element.y)

            # outTangents
            if i<elementsCount-1:
                nextElement = path.elementAt(i+1)
                if nextElement.type is QPainterPath.ElementType.CurveToElement:
                    outTangent = control.outTangent
                    outTangent.setLine(element.x, element.y, nextElement.x, nextElement.y)

            # inTangent
            if i>0:
                prevElement = path.elementAt(i-1)
                if element.type is QPainterPath.ElementType.CurveToDataElement and prevElement.type is QPainterPath.ElementType.CurveToDataElement:
                    inTangent = control.inTangent
                    inTangent.setLine(prevElement.x,prevElement.y, element.x, element.y)

    def destroyControls(self):
        raise NotImplementedError

    def sceneEventFilter(self, watched, event):
        if event.type() == QEvent.GraphicsSceneMouseMove:
            path = self.path()
            elementsCount = path.elementCount()
            i = watched.userData
            element = path.elementAt(i)

            # move point
            dx, dy = event.scenePos().x()-event.lastScenePos().x(), event.scenePos().y()-event.lastScenePos().y()
            path.setElementPositionAt(i, element.x+dx, element.y+dy)
            
            # move out tangent
            if i<elementsCount-1:
                nextElement = path.elementAt(i+1)
                if nextElement.type is QPainterPath.ElementType.CurveToElement:
                    path.setElementPositionAt(i+1, nextElement.x+dx, nextElement.y+dy)

            # move in tangent
            if i>0:
                prevElement = path.elementAt(i-1)
                if element.type is QPainterPath.ElementType.CurveToDataElement and prevElement.type is QPainterPath.ElementType.CurveToDataElement:
                    path.setElementPositionAt(i-1, prevElement.x+dx, prevElement.y+dy)

            # set the path
            self.setPath(path)

            # patch control points
            self.patchControls()

            self.pathChanged.emit()

        return True

if __name__ == "__main__":
    from viewer2D import Viewer
    app = QApplication.instance() or QApplication()
    viewer = Viewer()

    editor = PathEditor()
    path = QPainterPath()
    path.addEllipse(10,10,400,400)
    editor.setPath(path)

    def on_path_changed():
        print("path changed")
    editor.pathChanged.connect(on_path_changed)
    
    viewer.addItem(editor)
    viewer.show()
    app.exec_()