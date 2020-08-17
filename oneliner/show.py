from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class Worker(QThread):
	progress = Signal(int, object)
	ready = Signal()

	def __init__(self, f):
		super().__init__()
		self.f = f

	def run(self):
		for i, result in enumerate(self.f()):
			self.progress.emit( i, result) 
		self.ready.emit()

class Renderer(QGraphicsItem):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self._target=None

	def setTarget(self, target):
		self._target = target
		self.prepareGeometryChange()
		self.update()

	def paint(self, painter, option, widget):
		if isinstance(self._target, QPainterPath):
			pass
		else:
			fm = QFontMetrics(painter.font())
			painter.drawText(0,0,str(self._target))

	def boundingRect(self):
		if isinstance(self._target, QPainterPath):
			return QSize(0,0)
		else:
			font = QApplication.font()
			fm = QFontMetrics(font)
			bbox = fm.boundingRect( str(self._target))
			return bbox

def show(worker):
	app = QApplication.instance() or QApplication()
	renderer = Renderer()
	scene = QGraphicsScene()
	scene.addItem(renderer)
	viewer = QGraphicsView()
	viewer.setScene(scene)
	viewer.centerOn(renderer)
	viewer.show()
	worker.start()

	def show_progress(i, result):
		print(i, result)
		renderer.setTarget(result)
		viewer.centerOn(renderer.boundingRect().center())

	worker.progress.connect(show_progress)
	app.exec_() # FIXME: exit worker thread before quittint the application

if __name__ == "__main__":
	import time
	def doWork():
		for i in range(0,10):
			time.sleep(1)
			yield i

	show(Worker(doWork))