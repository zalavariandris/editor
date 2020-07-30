from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class Outliner(QWidget):
    selectionChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.list = QListWidget()
        self.list.itemSelectionChanged.connect(self.selectionChanged.emit)
        self.layout().addWidget(self.list)
    
    def addItem(self, item):
        self.list.addItem(item)

    def selection(self):
        return self.list.selectedItems()

if __name__ == "__main__":
    app = QApplication.instance() or QApplication()
    outliner = Outliner()
    outliner.show()
    outliner.addItem("item1")
    outliner.addItem("item2")
    def on_selection_changed():
        print("selection changed", outliner.selection())
        
    outliner.selectionChanged.connect(on_selection_changed)
    app.exec_()