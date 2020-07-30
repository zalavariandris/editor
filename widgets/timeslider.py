from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *

class Button(QPushButton):
	def __init__(self, text, parent=None):
		super().__init__(text=text, parent=parent)

	def sizeHint(self):
		return QSize(42, 42)


class Timeslider(QWidget):
	frameChanged = Signal()
	firstFrameChanged = Signal()
	lastFrameChanged = Signal()

	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setLayout( QVBoxLayout() )
		self.layout().setSpacing(0)
		self.settingsBar = QWidget()
		self.settingsBar.setLayout(QHBoxLayout())
		self.settingsBar.layout().setContentsMargins(6,6,6,6)
		self.sliderBar = QWidget()
		self.sliderBar.setLayout(QHBoxLayout())
		self.sliderBar.layout().setContentsMargins(6,6,6,6)
		self.buttonsBar = QWidget()
		self.buttonsBar.setLayout(QHBoxLayout())
		self.buttonsBar.layout().setContentsMargins(6,6,6,6)

		self.layout().addWidget(self.buttonsBar)
		self.layout().addWidget(self.sliderBar)
		self.layout().addWidget(self.settingsBar)

		# slider bar
		self.firstFrameSpinner = QSpinBox()
		self.lastFrameSpinner = QSpinBox()
		self.firstFrameSpinner.setMinimum(-99999)
		self.firstFrameSpinner.setMaximum(99999)
		self.lastFrameSpinner.setMinimum(-99999)
		self.lastFrameSpinner.setMaximum(99999)
		self.firstFrameSpinner.valueChanged.connect(lambda: self.setFirstFrame(self.firstFrameSpinner.value()))
		self.lastFrameSpinner.valueChanged.connect(lambda: self.setLastFrame(self.lastFrameSpinner.value()))

		self.slider = QSlider(orientation=Qt.Horizontal)
		self.slider.valueChanged.connect(lambda: self.setFrame(self.slider.value()))
		self.sliderBar.layout().addWidget(self.firstFrameSpinner)
		self.sliderBar.layout().addWidget(self.slider)
		self.sliderBar.layout().addWidget(self.lastFrameSpinner)
		
		# playback buttons bar

		self.playBackwardButton = Button("<")

		self.playForwardButton = Button(">")
		self.pauseButton = Button("||")
		self.stepForwardButton = Button("|>")
		self.stepBackwardButton = Button("<|")
		self.jumpToFirstFrameButton = Button("|<")
		self.jumpToLastFrameButton = Button(">|")

		self.buttonsBar.layout().addStretch()
		self.buttonsBar.layout().addWidget(self.jumpToFirstFrameButton)
		self.buttonsBar.layout().addWidget(self.stepBackwardButton)
		self.buttonsBar.layout().addWidget(self.playBackwardButton)
		self.buttonsBar.layout().addWidget(self.pauseButton)
		self.buttonsBar.layout().addWidget(self.playForwardButton)
		self.buttonsBar.layout().addWidget(self.stepForwardButton)
		self.buttonsBar.layout().addWidget(self.jumpToLastFrameButton)
		self.buttonsBar.layout().addStretch()
		
		
		# settings bar
		self.fpsSpinner = QSpinBox()
		
		self.playModeSelector = QComboBox()
		self.playModeSelector.addItems(["repeat", "bounce", "stop", "continue"])

		self.settingsBar.layout().addStretch()
		self.settingsBar.layout().addWidget(self.fpsSpinner)
		self.settingsBar.layout().addWidget(self.playModeSelector)

		# set defaults
		self.setFirstFrame(0)
		self.setLastFrame(100)
		self.setFps(24)

		self.stepForwardButton.clicked.connect(lambda: self.setFrame(self.frame()+1))
		self.stepBackwardButton.clicked.connect(lambda: self.setFrame(self.frame()-1))

		self.isPlaying = False
		self.playDirection = None
		self.timer = QTimer()

		def onTick():
			if self.playDirection == "Forward":
				
				if (self.frame()+1)>self.lastFrame():
					self.setFrame(self.firstFrame())
				else:
					self.setFrame(self.frame()+1)

			if self.playDirection == "Backward":
				
				if (self.frame()-1)<self.firstFrame():
					self.setFrame(self.lastFrame())
				else:
					self.setFrame(self.frame()-1)

		self.timer.timeout.connect(onTick)

		def startPlaying(direction="Forward"):
			self.playDirection = direction
			if not self.timer.isActive():
				self.timer.start(1000/self.fps())
				self.isPlaying = True

		def pausePlaying():
			if self.timer.isActive():
				self.timer.stop()


		self.playForwardButton.clicked.connect(lambda: startPlaying("Forward"))
		self.playBackwardButton.clicked.connect(lambda: startPlaying("Backward"))
		self.pauseButton.clicked.connect(pausePlaying)

		def updateFps():
			if self.timer.isActive():
				self.timer.stop()
				self.timer.start(1000/self.fps())

		self.fpsSpinner.valueChanged.connect(updateFps)

	def setFrame(self, frame):
		self.slider.setValue(frame)
		self.frameChanged.emit()

	def frame(self):
		return self.slider.value()

	def fps(self):
		return self.fpsSpinner.value()

	def setFps(self, fps):
		self.fpsSpinner.setValue(fps)

	def firstFrame(self):
		return self.slider.minimum()

	def setFirstFrame(self, firstFrame):
		self.firstFrameSpinner.setValue(firstFrame)
		self.slider.setMinimum(firstFrame)
		self.firstFrameChanged.emit()
		if firstFrame>=self.lastFrame():
			self.setLastFrame(firstFrame+1)


	def setLastFrame(self, lastFrame):
		self.lastFrameSpinner.setValue(lastFrame)
		
		self.slider.setMaximum(lastFrame)
		self.lastFrameChanged.emit()
		if lastFrame<=self.firstFrame():
			self.setFirstFrame(lastFrame-1)

		

	def lastFrame(self):
		return self.slider.maximum()


if __name__ == "__main__":
	app = QApplication()
	timeslider = Timeslider()
	timeslider.setFirstFrame(0)
	timeslider.setLastFrame(50)
	timeslider.show()
	timeslider.frameChanged.connect(lambda: print("frame:", timeslider.frame()))
	timeslider.firstFrameChanged.connect(lambda: print("first:", timeslider.firstFrame()))
	timeslider.lastFrameChanged.connect(lambda: print("last:", timeslider.lastFrame()))
	app.exec_()