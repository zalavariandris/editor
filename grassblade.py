from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import numpy as np
import inspect
from typing import Any
from nptyping import NDArray, Bool
import cv2

from utils import convert_cvImgToPixmap
from read import read
import pathlib

def tps(sourcePoints, targetPoints, img):
    # thinplate spline deform
    tps = cv2.createThinPlateSplineShapeTransformer()
    sshape = sourcePoints.reshape (1, -1, 2)
    tshape = targetPoints.reshape (1, -1, 2)
    matches = []
    for i in range(sshape.shape[1]):
        matches.append (cv2.DMatch (i, i, 0))

    tps.estimateTransformation(tshape.copy(), sshape.copy(), matches)
    return tps.warpImage(img)

def divideCurve(curve: QPainterPath, n: int)->NDArray[(2,Any)]:
    points = [curve.pointAtPercent(t) for t in np.linspace(0,1,9)][:-1]
    return np.array([[point.x(), point.y()] for point in points])


def evaluate(filePath: pathlib.Path, frame, sourcePath: QPainterPath, targetPath: QPainterPath)->NDArray[(2, Any), np.float32]:
    img = read(filePath, frame)
    # return img

    # get points
    sourcePoints = divideCurve(sourcePath, 10)
    targetPoints = divideCurve(targetPath, 10)

    deformed = tps(sourcePoints, targetPoints, img)
    return deformed


class GBModel(QObject):
    filePathChanged = Signal()
    frameChanged = Signal()
    sourcePathChanged = Signal()
    targetPathChanged = Signal()
    ouputChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.filePath = ""
        self.frame = 0
        self.sourcePath = QPainterPath()
        self.sourcePath.addEllipse(100, 100, 300, 300)
        self.targetPath = QPainterPath()
        self.targetPath.addEllipse(100, 100, 100, 300)

        self.filePathChanged.connect(self.evaluate)
        self.frameChanged.connect(self.evaluate)
        self.sourcePathChanged.connect(self.evaluate)
        self.targetPathChanged.connect(self.evaluate)

        self.timer = QTimer()
        def animate():
            print("animate", self.frame)
            self.frame+=1

        self.timer.timeout.connect(animate)
        self.timer.start(1000/24)

    # inputs
    @property
    def sourcePath(self):
        return self._sourcePath

    @sourcePath.setter
    def sourcePath(self, sourcePath):
        self._sourcePath = sourcePath
        self.sourcePathChanged.emit()

    @property
    def targetPath(self):
        return self._targetPath

    @targetPath.setter
    def targetPath(self, targetPath):
        self._targetPath = targetPath
        self.targetPathChanged.emit()
    
    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, frame):
        self._frame = frame
        self.frameChanged.emit()
    

    # evaluate
    def evaluate(self):
        self.output = evaluate(self.filePath, self.frame, self.sourcePath, self.targetPath)
        self.ouputChanged.emit()

from widgets.appwindow import AppWindow
from widgets.patheditor import PathEditor


class GBController(QObject):
    def __init__(self):
        self.view = AppWindow()
        """ output viewer """
        self.pixmapItem = QGraphicsPixmapItem()
        self.view.viewer.addItem(self.pixmapItem)

        """ input editors """
        self.sourcePathEditor = PathEditor()
        self.view.viewer.addItem(self.sourcePathEditor)

        self.targetPathEditor = PathEditor()
        self.view.viewer.addItem(self.targetPathEditor)

        """ create model"""
        self.model = GBModel()
        self.model.filePath = "C:/Users/andris/Desktop/2020 Paks/Grassblade/footage/IMG_9148.MOV"
        self.model.ouputChanged.connect(self.patch)

        """sync model-view"""
        def updateSourcePath():
            self.model.sourcePath = self.sourcePathEditor.path()
        self.sourcePathEditor.pathChanged.connect(updateSourcePath)

        def updateTargetPath():
            self.model.targetPath = self.targetPathEditor.path()
        self.targetPathEditor.pathChanged.connect(updateTargetPath)
        self.model.ouputChanged.connect(self.patch)

        """ fire up """
        self.view.show()
        self.model.evaluate()

    def patch(self):
        # source editors """
        self.sourcePathEditor.setPath(self.model.sourcePath)
        self.targetPathEditor.setPath(self.model.targetPath)

        """ output viewer """
        img = self.model.output
        pixmap = convert_cvImgToPixmap(img)
        self.pixmapItem.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication.instance() or QApplication()
    controller = GBController()
    app.exec_()



