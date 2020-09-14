class Mesh:
    def __init__(self, transform, material, geometry):
        self._transform = transform
        self._material = material
        self._geometry = geometry

        self.buffers = ()

    @property
    def transform(self):
        return self._transform

    @property
    def material(self):
        return self._material

    @property
    def geometry(self):
        return self._geometry

