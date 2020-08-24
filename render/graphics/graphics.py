class Material:
	"""PBR material"""
	def __init__(self):
		self.albedo
		self.roughness
		self.metalness
		self.emission
		self.opacity
		self.normal

		self.albedoMap
		self.roughnessMap
		self.metalnessMap
		self.emissionMap
		self.opacityMap
		self.normalMap


class Geometry:
	def __init__(self):
		self.positions=np.array()
		self.indices=np.array()
		self.normals=np.array()
		self.colors=np.array()
		self.uvs=np.array()

	@staticmethod
	def box():
		pass

	def sphere():
		pass

	def plane():
		pass

	def from_trimesh():
		pass


class Mesh:
	def __init__(self, geometry, material):
		self.parent = None
		self.children = []

	def draw(self):
		pass

	def setup(self):
		pass





