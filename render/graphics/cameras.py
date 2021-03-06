import glm
import numpy as np

class OrthographicCamera:
	def __init__(self, transform, width, height, near, far):
		self.transform = transform
		self.width = width
		self.height = height
		self.near = near
		self.far = far

	@property
	def position(self):
		return self.transform[3].xyz

	@position.setter
	def position(self, value):
		self.transform[3].xyz = value

	@property
	def projection(self):
		return glm.ortho(-self.width/2, self.width/2, -self.height/2, self.height/2, self.near, self.far)

	@property
	def view(self):
		return glm.inverse(self.transform)


class PerspectiveCamera:
	def __init__(self, transform, fovy, aspect, near, far):
		self.transform = transform
		self.fovy = fovy
		self.aspect = aspect
		self.near = near
		self.far = far

	@property
	def position(self):
		return self.transform[3].xyz

	@position.setter
	def position(self, value):
		self.transform[3].xyz = value

	@property
	def projection(self):
		return glm.perspective(self.fovy, self.aspect, self.near, self.far)

	@property
	def view(self):
		return glm.inverse(self.transform)
	

class Camera360:
    def __init__(self, transform, near, far):
        self.transform = transform
        self.near = near
        self.far = far

    @property
    def projection(self):
        return glm.perspective(glm.radians(90.0), 1.0, self.near, self.far)

    @property
    def views(self):
        views = []
        views.append(glm.lookAt(self.position, self.position + glm.vec3( 1, 0, 0), glm.vec3(0,-1, 0)))
        views.append(glm.lookAt(self.position, self.position + glm.vec3(-1, 0, 0), glm.vec3(0,-1, 0)))
        views.append(glm.lookAt(self.position, self.position + glm.vec3( 0, 1, 0), glm.vec3(0, 0, 1)))
        views.append(glm.lookAt(self.position, self.position + glm.vec3( 0,-1, 0), glm.vec3(0, 0,-1)))
        views.append(glm.lookAt(self.position, self.position + glm.vec3( 0, 0, 1), glm.vec3(0,-1, 0)))
        views.append(glm.lookAt(self.position, self.position + glm.vec3( 0, 0,-1), glm.vec3(0,-1, 0)))

        views = np.array([np.array(m) for m in views])
        return views

    @property
    def position(self):
        return self.transform[3].xyz

    @position.setter
    def position(self, value):
        self.transform[3].xyz = value