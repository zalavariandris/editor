import numpy as np

def render(scene)->np.ndarray:
	pass

from editor.render.window import GLFWViewer


width, height = 1024, 768
window = GLFWViewer(width, height, (0.6, 0.7, 0.7, 1.0))

with window:
	#setup
	pass

with window:
	while not window.should_close():
		# draw
		pass


