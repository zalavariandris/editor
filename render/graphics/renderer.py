from editor.render import gloo
from editor.render.with_glfw import Window
import numpy as np
from editor.render import helpers
from OpenGL.GL import *
import glm
import math
from editor.render.helpers import orbit

class Scene:
	def __init__(self):
		self.children = []

	def add(self, obj):
		self.children.append(obj)


class Material:
	pass


class Texture:
	pass


class Transform:
	pass


class Geometry:
	def __init__(self):
		self.vertices = np.array([], dtype=np.float32).reshape(-1,3)
		self.indices = np.array([], dtype=np.uint).reshape(-1,3)

		# visuals
		self.normals = np.array([], dtype=np.float32).reshape(-1,3)
		self.uvs = np.array([], dtype=np.float32).reshape(-1,2)
		self.colors = np.array([], dtype=np.float32).reshape(-1,3)

	@staticmethod
	def box():
		geo = Geometry()
		data = helpers.box()

		geo.vertices = data['positions']
		geo.indices = data['indices']
		geo.normals = data['normals']
		geo.colors = data['colors']
		geo.uvs = data['uvs']
		return geo

	def sphere():
		geo = Geometry()
		data = helpers.sphere()

		geo.vertices = data['positions']
		geo.indices = data['indices']
		geo.normals = data['normals']
		geo.colors = data['colors']
		geo.uvs = data['uvs']
		return geo


class RenderItem():
	pass

class Mesh(RenderItem):
	def __init__(self, geometry, transform, material):
		self.geometry = geometry
		self.transform = transform
		self.material = material

	def draw(self):
		pass

class Camera(RenderItem):
	pass

import time
class Viewer:
	def __init__(self, scene):
		self.width, self.height = 640, 480
		self.window = Window(self.width, self.height, (1,1,1,1))

		@self.window.addEventListener("mousemove")
		def mousemove(x, y, dx, dy):
			if self.window.get_mouse_button(0):
				self.view_matrix = orbit(self.view_matrix, dx*2,dy*2)

		@self.window.addEventListener("mousebutton")
		def mousebutton(button, action, modifiers):
			pass

		@self.window.addEventListener("scroll")
		def scroll(dx, dy):
			s = 1+dy/10
			self.view_matrix = glm.scale(self.view_matrix, (s,s,s))

		@self.window.addEventListener("resize")
		def resize(w, h):
			glViewport(0, 0, w, h)
			self.projection_matrix = glm.perspective(math.radians(60), w/h, 1, 100)
			
			# redraw while resizing
			self.draw()
			self.window.swap_buffers()
			# self.window.poll_events()
			

		self.scene = scene
		self.items = dict()

		with self.window:
			self.setup()
			self._start()


	def _start(self):
		while not self.window.should_close():
			self.draw()
			self.window.swap_buffers()
			Window.poll_events()

	def setup(self):
		for mesh in self.scene.children:
			renderitem = {
				'shader': gloo.Shader(),
				'material':{
					'ambient': (0.1, 0.1, 0.1),#glm.vec3(0.1),
					'diffuse': glm.vec3(0.6, 0.5, 0.1),
					'specular': glm.vec3(1.0, 1.0, 0.0),
					'shiness': 100.0
				},
				'attributes':{
					'vertices': gloo.VertexBuffer(mesh.geometry.vertices),
					'indices': gloo.IndexBuffer(mesh.geometry.indices),
					'normals': gloo.VertexBuffer(mesh.geometry.normals)
				}
			}
			self.items[mesh] = renderitem

		self.shader = gloo.Shader()
		self.view_matrix = glm.lookAt( glm.vec3(0, 1,4), glm.vec3(0,0,0), glm.vec3(0,1,0) )
		self.projection_matrix = glm.perspective(math.radians(60), self.width/self.height, 0.1, 100)

	def draw(self):
		glEnable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		for renderitem in self.items.values():
			self.draw_item(renderitem)

	def draw_item(self, renderitem):
		with renderitem['shader'] as shader, gloo.VAO() as vao:
			# bind attributes
			indexBuffer = renderitem['attributes']['indices']

			positionBuffer = renderitem['attributes']['vertices']
			location = shader.get_attribute_location('position')
			vao.enable_vertex_attribute(location)
			vao.set_vertex_attribute(location, positionBuffer, 3, GL_FLOAT)

			positionBuffer = renderitem['attributes']['normals']
			location = shader.get_attribute_location('normal')
			vao.enable_vertex_attribute(location)
			vao.set_vertex_attribute(location, positionBuffer, 3, GL_FLOAT)

			# Uniforms
			# camera
			shader.set_uniform('projectionMatrix', self.projection_matrix)
			shader.set_uniform('viewMatrix', self.view_matrix)
			shader.set_uniform('viewPos', np.linalg.inv(self.view_matrix)[3][:3])

			# lights
			lightPos = glm.vec3(math.sin(time.time()*5)*10, 2,0)
			shader.set_uniform('light.position', lightPos)
			shader.set_uniform('light.ambient', glm.vec3(1.0))
			shader.set_uniform('light.diffuse', glm.vec3(1.0))
			shader.set_uniform('light.specular', glm.vec3(1.0))

			# transform
			shader.set_uniform('modelMatrix', np.eye(4))

			# material
			shader.set_uniform('material.useVertexColor', False)
			shader.set_uniform('material.useDiffuseMap', False)
			shader.set_uniform('material.ambient', renderitem['material']['ambient'])
			shader.set_uniform('material.diffuse', renderitem['material']['diffuse'])
			shader.set_uniform('material.specular', renderitem['material']['specular'])
			shader.set_uniform('material.shiness', renderitem['material']['shiness'])
			

			with indexBuffer:
				count = indexBuffer.count
				glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)

if __name__ == "__main__":
	mesh = Mesh(
		geometry=Geometry.sphere(), 
		transform=np.eye(4), 
		material=Material()
	)

	scene = Scene()
	scene.add(mesh)
	viewer = Viewer(scene)