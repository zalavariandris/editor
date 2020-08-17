import cv2
class VideoWriter():
	def __init__(self, filename, fps=24, fourcc="mp4v"):
		self.filename = filename
		self._cap = None
		self.fps = fps
		self.fourcc = fourcc

	def __enter__(self):
		print("enter")
		return self

	def write(self, image):
		if self._cap is None:
			fourcc = cv2.VideoWriter_fourcc(*self.fourcc)
			fps = self.fps
			height, width, channels = image.shape
			self._cap = cv2.VideoWriter(str(self.filename), fourcc, fps, (width, height))

		self._cap.write(image)

	def __exit__(self, type, value, traceback):
		print("exit")
		if self._cap is not None:
			self._cap.release()


if __name__ == "__main__":
	print("VideoWriter example")
