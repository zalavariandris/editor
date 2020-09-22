import glm
from . import Material
import uuid

class Mesh:
    def __init__(self, geometry, transform=glm.mat4(1), material=Material(), name=uuid.uuid4().hex):
        self._transform = transform
        self._material = material
        self._geometry = geometry

        self.buffers = ()
        self.name = name

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = value

    @property
    def material(self):
        return self._material

    @property
    def geometry(self):
        return self._geometry


