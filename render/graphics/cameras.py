import glm

class OrthographicCamera:
	def __init__(self, transform, width, height, near, far):
		self.transform = transform
		self.width = width
		self.height = height
		self.near = near
		self.far = far

	@property
	def projection(self):
		return glm.ortho(-self.width/2, self.width/2, -self.height/2, self.height/2, self.near, self.far)

	@property
	def view(self):
		return self.transform
	
class PerspectiveCamera:
	def __init__(self, transform, fovy, aspect, near, far):
		self.transform = transform
		self.fovy = fovy
		self.aspect = aspect
		self.near = near
		self.far = far

	@property
	def projection(self):
		return glm.perspective(self.fovy, self.aspect, self.near, self.far)

	@property
	def view(self):
		return glm.inverse(self.transform)
	