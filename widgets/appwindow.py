
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from .viewer2D import Viewer
from .inspector import Inspector
from .outliner import Outliner

class AppWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # viewer
        self.viewer = Viewer()
        self.setCentralWidget(self.viewer)

        # inspector
        self.inspector = Inspector()
        rightDock = QDockWidget('Inspector')
        rightDock.setWidget(self.inspector)
        self.addDockWidget(Qt.RightDockWidgetArea, rightDock)

        # outliner
        self.outliner = Outliner()
        leftDock = QDockWidget("Outliner")
        leftDock.setWidget(self.outliner)
        self.addDockWidget(Qt.LeftDockWidgetArea, leftDock)

if __name__ == "__main__":    
    app  = QApplication.instance() or QApplication()
    window = AppWindow()
    window.show()
    app.exec_()