from OpenGL.GL import *
import numpy as np
from editor.render.window import GLFWViewer
from editor.render.puregl import imdraw, program, texture
from editor.render import glsl
from editor.render import assets

import logging
logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')


class Viewer:
	def __init__(self):
		self.width = 1024
		self.height = 768
		self.window = GLFWViewer(self.width, self.height, (0.2, 0.2, 0.2, 1.0))

		self.matcap_img = assets.imread("matcap/jeepster_skinmat2.jpg").astype(np.float32)/255
		# self.matcap_img = assets.imread("container2_axis.png").astype(np.float32)[...,[0,1,2]]/255
		self.matcap_img = np.flip(self.matcap_img, 0)

	def setup(self):
		with self.window:
			glEnable(GL_DEPTH_TEST)
			glEnable(GL_CULL_FACE)
			glEnable( GL_PROGRAM_POINT_SIZE )

			self.prog = program.create(*glsl.read("matcap"))
			self.matcap_tex = texture.create(self.matcap_img, 0, GL_RGB)

	def resize(self):
		with self.window:
			pass

	def draw(self):
		with self.window as window:
			glViewport(0,0,self.width, self.height)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			with program.use(self.prog) as prog:
				program.set_uniform(prog, 'projectionMatrix', window.projection_matrix)
				program.set_uniform(prog, 'viewMatrix', window.view_matrix)
				program.set_uniform(prog, 'modelMatrix', np.eye(4))
				glBindTexture(GL_TEXTURE_2D, self.matcap_tex)
				program.set_uniform(prog, 'matCap', 0)
				imdraw.torusknot(prog)

			window.swap_buffers()
			GLFWViewer.poll_events()

	def start(self):
		self.setup()
		
		while not self.window.should_close():
			self.draw()

if __name__ == "__main__":
	viewer = Viewer()
	viewer.start()

