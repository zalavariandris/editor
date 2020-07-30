from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class FileSelector(QWidget):
	fileSelected = Signal()
	def __init__(self):
		super().__init__()
		self.setLayout(QHBoxLayout())
		self.button = QPushButton("Choose file")
		self.button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
		self.label = QLabel("No file choosen")
		self.label.setMinimumSize(QSize(10, 10))
		self.label.setSizePolicy( QSizePolicy.Maximum, QSizePolicy.Preferred )
		self.layout().addWidget(self.button)
		self.layout().addWidget(self.label)

		self.button.clicked.connect(self.selectFile)

	def selectFile(self):
		self.path, selectedFilter = QFileDialog.getOpenFileName()
		if self.path is not "":
			self.label.setText(self.path)
			self.label.setToolTip(self.path)
			self.fileSelected.emit()

	def file(self):
		return self.path




if __name__ == "__main__":
	app = QApplication()
	inputFile = FileSelector()
	inputFile.show()
	def on_file_selected():
		print(inputFile.file())
	inputFile.fileSelected.connect(on_file_selected)
	app.exec_()