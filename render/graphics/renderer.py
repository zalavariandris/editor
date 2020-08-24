from editor.render import gloo
from editor.render.gloo_with_glfw import Window
import numpy as np
from editor.render import helpers
from OpenGL.GL import *
import glm
import math
from editor.render.helpers import orbit
from PIL import Image
from pathlib import Path

class Scene:
	def __init__(self):
		self.children = []

	def add(self, obj):
		self.children.append(obj)

	def find_all(self, klass):
		for child in self.children:
			if isinstance(child, klass):
				yield child


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


class RenderItem:
	def setup(self):
		raise NotImplementedError("subclasses needs to reimplement setup method")
		self.shader = None
		self.uniforms = {}
		self.attributes = {}

	def draw(self, projection_matrix, view_matrix, scene):
		raise NotImplementedError("subclasses needs to reimplement setup method")
		with shader:
			pass


class Mesh(RenderItem):
	def __init__(self, geometry: dict, transform: np.ndarray, material: dict):
		self.geometry = geometry
		self.transform = transform
		self.material = material

	def setup(self):
		self.shader=gloo.Shader(Path("../shader.vert").read_text(), Path('../shader.frag').read_text())
		self.uniforms={
			'ambient': self.material['ambient'],
			'diffuse': self.material['diffuse'],
			'specular': self.material['specular'],
			'shiness': self.material['shiness'],
			'diffuseMap': gloo.Texture.from_data(self.material['diffuseMap'], slot=0),
			'specularMap': gloo.Texture.from_data(self.material['specularMap'], slot=1)
		}
		self.attributes={
			'vertices': gloo.VBO(self.geometry.vertices),
			'indices': gloo.EBO(self.geometry.indices),
			'normals': gloo.VBO(self.geometry.normals),
			'uvs': gloo.VBO(self.geometry.uvs),
		}

	def draw(self, projection_matrix, view_matrix, scene):
		with self.shader as shader, gloo.VAO() as vao:
			# bind attributes
			indexBuffer = self.attributes['indices']

			positionBuffer = self.attributes['vertices']
			location = shader.get_attribute_location('position')
			vao.enable_vertex_attribute(location)
			vao.set_vertex_attribute(location, positionBuffer, 3, GL_FLOAT)

			normalBuffer = self.attributes['normals']
			location = shader.get_attribute_location('normal')
			vao.enable_vertex_attribute(location)
			vao.set_vertex_attribute(location, normalBuffer, 3, GL_FLOAT)

			uvBuffer = self.attributes['uvs']
			location = shader.get_attribute_location('uv')
			vao.enable_vertex_attribute(location)
			vao.set_vertex_attribute(location, uvBuffer, 2, GL_FLOAT)

			# 
			# Uniforms
			#
			# Camera
			shader.set_uniform('projectionMatrix', projection_matrix)
			shader.set_uniform('viewMatrix', view_matrix)
			shader.set_uniform('viewPos', np.linalg.inv(view_matrix)[3][:3])

			# Lights
			# point lights
			for i, light in enumerate(scene.find_all(PointLight)):
				pos = glm.vec3(0,math.sin(time.time()*3)*10+10.5,0);
				shader.set_uniform('pointLights[{}].position'.format(i), light.position)
				shader.set_uniform('pointLights[{}].ambient'.format(i), light.ambient)
				shader.set_uniform('pointLights[{}].diffuse'.format(i), light.diffuse)
				shader.set_uniform('pointLights[{}].specular'.format(i), light.specular)
				shader.set_uniform('pointLights[{}].constant'.format(i), light.constant)
				shader.set_uniform('pointLights[{}].linear'.format(i), light.linear)
				shader.set_uniform('pointLights[{}].quadratic'.format(i), light.quadratic)

			# directional lights
			for light in scene.find_all(DirectionalLight):
				shader.set_uniform('sun.direction', light.direction)
				shader.set_uniform('sun.ambient', light.ambient)
				shader.set_uniform('sun.diffuse', light.diffuse)
				shader.set_uniform('sun.specular', light.specular)

			# spotlights


			# transform
			shader.set_uniform('modelMatrix', np.eye(4))

			# material
			shader.set_uniform('material.useVertexColor', False)
			if self.uniforms['diffuseMap'] is not None:
				shader.set_uniform('material.useDiffuseMap', True)
				shader.set_uniform('material.diffuseMap', self.uniforms['diffuseMap'].texture_unit)
			if self.uniforms['specularMap'] is not None:
				shader.set_uniform('material.useSpecularMap', True)
				shader.set_uniform('material.specularMap', self.uniforms['specularMap'].texture_unit)

			shader.set_uniform('material.ambient', self.uniforms['ambient'])
			shader.set_uniform('material.diffuse', self.uniforms['diffuse'])
			shader.set_uniform('material.specular', self.uniforms['specular'])
			shader.set_uniform('material.shiness', self.uniforms['shiness'])
			

			with indexBuffer:
				count = indexBuffer.count
				if self.uniforms['diffuseMap']:
					self.uniforms['diffuseMap'].bind()
				if self.uniforms['specularMap']:
					self.uniforms['specularMap'].bind()
				glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)


class Light:
	def __init__(self, ambient=glm.vec3(1.0), diffuse=glm.vec3(1.0), specular=glm.vec3(1.0)):
		self.ambient=ambient
		self.diffuse=diffuse
		self.specular=specular

class DirectionalLight(Light):
	def __init__(self, ambient=glm.vec3(1.0), diffuse=glm.vec3(1.0), specular=glm.vec3(1.0), 
		direction=glm.vec3(0, -1, 0)):
		super().__init__(ambient, diffuse, specular)
		self.direction = direction

class PointLight(Light):
	def __init__(self, ambient=glm.vec3(1.0), diffuse=glm.vec3(1.0), specular=glm.vec3(1.0), 
		position=glm.vec3(0),
		constant=1.0, linear=0.09, quadratic=0.032):
		super().__init__(ambient, diffuse, specular)
		self.position=position

		self.constant=1.0
		self.linear=0.09
		self.quadratic=0.032

class SpotLight(Light):
	def __init__(self, ambient=1.0, diffuse=1.0, specular=1.0, 
		position=glm.vec3(0), direction=glm.vec3(0,-1,0),
		constant=1.0, linear=0.09, quadratic=0.032):
		super().__init__(ambient, diffuse, specular)
		self.position = glm.vec3(0)
		self.direction = glm.vec3(0,-1,0)

		self.constant=constant
		self.linear=linear
		self.quadratic=quadratic


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
		# trasnfer mesh attributes to render item
		for mesh in self.scene.find_all(Mesh):
			mesh.setup()
			# renderitem = RenderItem()
			# renderitem.setup(mesh)
			# self.items[mesh] = renderitem

		self.view_matrix = glm.lookAt( glm.vec3(0, 1,4), glm.vec3(0,0,0), glm.vec3(0,1,0) )
		self.projection_matrix = glm.perspective(math.radians(60), self.width/self.height, 0.1, 100)

	def draw(self):
		glEnable(GL_CULL_FACE)
		glCullFace(GL_BACK)
		glEnable(GL_DEPTH_TEST)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		for renderitem in self.scene.find_all(RenderItem):
			renderitem.draw(self.projection_matrix, self.view_matrix, self.scene)
		

if __name__ == "__main__":
	scene = Scene()
	diff_texture_data = np.array(Image.open("../../assets/container2.png"))[:,:,:3].astype(np.float32)/255.0
	diff_texture_data=diff_texture_data[:,:,::-1] #RGB->BGR
	spec_texture_data = np.array(Image.open("../../assets/container2_specular.png"))[:,:,:3].astype(np.float32)/255.0
	spec_texture_data=spec_texture_data[:,:,::-1] #RGB->BGR
	mesh = Mesh(
		geometry=Geometry.box(), 
		transform=np.eye(4), 
		material={
			'ambient': (0.1, 0.1, 0.1),#glm.vec3(0.1),
			'diffuse': (0.6, 0.5, 0.1),
			'specular': (0.3, 0.3, 0.3),
			'shiness': 1.0,
			'diffuseMap': diff_texture_data,
			'specularMap': spec_texture_data
		}
	)
	scene.add(mesh)
	scene.add(DirectionalLight(direction=glm.vec3(1,-1,-1)))
	scene.add(PointLight(position=glm.vec3(-1,0,0)))
	viewer = Viewer(scene)