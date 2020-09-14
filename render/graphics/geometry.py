from editor.render import puregl


class Geometry:
    def __init__(self, positions, normals, uvs, indices):
        self._positions = positions
        self._normals = normals
        self._uvs = uvs
        self._indices = indices

    @property
    def positions(self):
        return self._positions

    @property
    def uvs(self):
        return self._uvs

    @property
    def normals(self):
        return self._normals

    @property
    def indices(self):
        return self._indices

    @classmethod
    def cube(cls):
        positions, normals, uvs, indices = puregl.geo.cube()
        return cls(positions, normals, uvs, indices)

    @classmethod
    def sphere(cls):
        positions, normals, uvs, indices = puregl.geo.sphere()
        return cls(positions, normals, uvs, indices)

    @classmethod
    def plane(cls):
        positions, normals, uvs, indices = puregl.geo.plane()
        return cls(positions, normals, uvs, indices)