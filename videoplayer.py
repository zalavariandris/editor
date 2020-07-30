from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

def convert_cvImgToPixmap(cvImg):
    # convert to pixmap
    height, width, channel = cvImg.shape
    bytesPerLine = 3 * width
    qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_RGB888)
    return QPixmap.fromImage(qImg)

import cv2
class ReadNode(QObject):
    frameChanged = Signal()
    pathChanged = Signal()
    imageChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._frame = 0
        self._path = None
        self._cap = None
        self.image = None
        self.dirty = False

    def setPath(self, path):
        if self._path == path:
            return

        self._cap = cv2.VideoCapture(path)
        if not self._cap.isOpened():
            self._cap = None
            return

        self._path = path
        self.dirty = True
        self.pathChanged.emit()
        
    def path(self):
        return self._path

    def setFrame(self, frame):
        if self._frame == frame:
            return
        self.dirty = True

        self._frame = frame
        self.frameChanged.emit()

    def frame(self):
        return self._frame

    def evaluate(self):
        if self.path() is None:
            return

        # if self.frame() is self._cap.get(cv2.CAP_PROP_POS_FRAMES-1):
        #     return
        if self._cap.get(cv2.CAP_PROP_POS_FRAMES)!=self._frame:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, self._frame)
        ret, cvImg = self._cap.read()

        if not ret:
            return

        self.image = cvImg
        self.imageChanged.emit()
        self.dirty = False


class TimeNode(QObject):
    frameChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._frame = 0

    def frame(self):
        return self._frame

    def setFrame(self, frame):
        self._frame = frame
        self.frameChanged.emit()


class Collection(QObject):
    itemsChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._items = []

    def append(self, item):
        self._items.append(item)
        self.itemsChanged.emit()

    def remove(self, item):
        self._items.remove(item)
        self.itemsChanged.emit()

    def setItems(self, items):
        self._items = items
        self.itemsChanged.emit()

    def items(self):
        return self._items


if __name__ == "__main__":
    """ create model """
    scene = Collection()
    timeNode = TimeNode()
    readNode = ReadNode()
    scene.append(timeNode)
    scene.append(readNode)

    v = 0
    def evaluate():
        global v
        print("evaluate", v); v+=1
        """ Update links """
        # timeNode.frame to readNode.frame
        readNode.setFrame( timeNode.frame() )

        """ Evaluate dirty nodes """
        if readNode.dirty:
            readNode.evaluate()

    """ trigger evaluate when nodes get dirty """
    timeNode.frameChanged.connect(evaluate)
    readNode.pathChanged.connect(evaluate)

    """ Create UI """
    from editor.widgets.appwindow import AppWindow
    from editor.widgets.inspector import InspectorPanel
    from editor.widgets.patheditor import PathEditor
    from editor.widgets.fileselector import FileSelector
    from editor.widgets.timeslider import Timeslider
    app = QApplication.instance() or QApplication()
    window = AppWindow()

    """ outliner """
    for node in scene.items():
        window.outliner.addItem(node.__class__.__name__)

    """ inspector """
    for node in scene.items():
        if node.__class__ is TimeNode:
            # time node
            timePanel = InspectorPanel()
            timePanel.setTitle("Time")
            timePanel.addRow("frame", Timeslider(), lambda spinner: spinner.frame, lambda spinner: spinner.frameChanged)
            window.inspector.addPane(timePanel)

            # sync view to model
            timePanel.valueChanged.connect(lambda: timeNode.setFrame(timePanel.fieldAt(0).frame()))

        if node.__class__ is ReadNode:
            # read node
            readPanel = InspectorPanel()
            readPanel.setTitle("Read")
            readPanel.addRow("file", FileSelector(), lambda field: field.file, lambda field: field.fileSelected)
            window.inspector.addPane(readPanel)

            # sync view to model
            readPanel.valueChanged.connect(lambda: readNode.setPath(readPanel.fieldAt(0).file() ))

    """ viewer """
    for node in scene.items():
        if node.__class__ is TimeNode:
            pass

        if node.__class__ is ReadNode:
            readGraphics = QGraphicsPixmapItem()
            window.viewer.addItem(readGraphics)

            # sync view to model
            def syncReadGraphics():
                if readNode.image is not None:
                    readGraphics.setPixmap( convert_cvImgToPixmap(readNode.image) )
            readNode.imageChanged.connect(syncReadGraphics)

    """ node editor """
    window.show()
    evaluate()
    app.exec_()





