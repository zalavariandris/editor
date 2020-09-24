import pyglet

from .window import window
from editor.render import puregl

class Viewer(Window):
	def __init__(self, width, height):
		super().__init__(width, height)
		self.renderer = DeferredPBRRenderer(self.width, self.height)

		@self.on_draw
		def draw():
			beauty = self.renderer.render(self.scene, self.camera)
			puregl.imdraw.texture(beauty, (0,0,self.width, self.height))
			puregl.imdraw.axis(window.camera.projection, window.camera.view)

	def start(self, worker=False):
		
