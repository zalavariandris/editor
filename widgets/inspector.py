from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class InspectorPanel(QWidget):
    valueChanged = Signal()
    def __init__(self, title="", parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.viewport = QWidget()
        self.viewport.setLayout(QFormLayout())
        self.header = QLabel(title)
        self.layout().addWidget(self.header)
        self.layout().addWidget(self.viewport)
        self.rows = []

    def addRow(self, label, field, value, signal):
        self.viewport.layout().addRow(label, field)
        self.rows.append(field)
        signal(field).connect(self.valueChanged)

    def setTitle(self, title):
        self.header.setText(title)

    def title(self):
        return self.header.text()

    def fieldCount(self):
        return len(self.rows)

    def fieldAt(self, idx):
        return self.rows[idx]

    def labelForField(self, field):
        return self.viewport.layout().labelForField(field)


class Inspector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

    def addPane(self, pane):
        self.layout().addWidget(pane)


if __name__ == "__main__":
    app = QApplication.instance() or QApplication()
    inspector = Inspector()
    inspector.show()
    inspector.setWindowTitle("Inspector")

    pane1 = InspectorPanel()
    pane1.setTitle("Pane1")
    pane1.addRow("path", QLineEdit(), lambda field: field.text, lambda field: field.textChanged)
    pane1.addRow("frame", QSpinBox(), lambda field: field.value, lambda field: field.valueChanged)
    
    pane2 = InspectorPanel()
    pane2.setTitle("Pane2")
    pane2.addRow("frame", QSpinBox(), lambda field: field.value, lambda field: field.valueChanged)

    inspector.addPane(pane1)
    inspector.addPane(pane2)

    def on_panel1_changed():
        print("=",pane1.title(),"=")
        path = pane1.fieldAt(0).text()
        print("- path:", path)

        field = pane1.fieldAt(1)
        print("- frame:", field.value())

        print()
        
    pane1.valueChanged.connect(on_panel1_changed)
    app.exec_()