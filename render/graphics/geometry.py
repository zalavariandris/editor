from editor.render import puregl
from OpenGL.GL import *


class Geometry:
    def __init__(self, positions, normals, uvs, indices):
        self._positions = positions
        self._normals = normals
        self._uvs = uvs
        self._indices = indices
        self._needs_setup = True

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

    def _setup(self):
        # geometry
        positions = self.positions
        uvs = self.uvs
        normals = self.normals
        indices = self.indices

        # setup VAO
        vao = glGenVertexArrays(1)

        # create VBOs
        pos_vbo, uv_vbo, norm_vbo = glGenBuffers(3)  # FIXME: use single vbo for positions and vertices

        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glBufferData(GL_ARRAY_BUFFER, positions.nbytes, positions, GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
        glBufferData(GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, norm_vbo)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)

        # create EBO
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        # pass to self
        self._vao = vao
        self._ebo = ebo
        self._vbos = pos_vbo, uv_vbo, norm_vbo

        self._needs_setup = False

    def _draw(self, prog):
        if self._needs_setup:
            self._setup()

        vao = self._vao
        ebo = self._ebo
        pos_vbo, uv_vbo, norm_vbo = self._vbos

        # attach VBOs
        glBindVertexArray(vao)

        position_location = glGetAttribLocation(prog, 'position')
        glBindBuffer(GL_ARRAY_BUFFER, pos_vbo)
        glVertexAttribPointer(position_location, 3, GL_FLOAT, False, 0, None)
        glEnableVertexAttribArray(position_location)

        uv_location = glGetAttribLocation(prog, 'uv')
        if uv_location >= 0:
            glBindBuffer(GL_ARRAY_BUFFER, uv_vbo)
            glVertexAttribPointer(uv_location, 2, GL_FLOAT, False, 0, None)
            glEnableVertexAttribArray(uv_location)

        norm_location = glGetAttribLocation(prog, 'normal')
        if norm_location >= 0:
            glBindBuffer(GL_ARRAY_BUFFER, norm_vbo)
            glVertexAttribPointer(norm_location, 3, GL_FLOAT, False, 0, None)
            glEnableVertexAttribArray(norm_location)

        #
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glDrawElements(GL_TRIANGLES, self.indices.size, GL_UNSIGNED_INT, None)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    @classmethod
    def cube(cls):
        positions, normals, uvs, indices = imdraw.geo.cube()
        return cls(positions, normals, uvs, indices)

    @classmethod
    def sphere(cls):
        positions, normals, uvs, indices = imdraw.geo.sphere()
        return cls(positions, normals, uvs, indices)

    @classmethod
    def plane(cls):
        positions, normals, uvs, indices = imdraw.geo.plane()
        return cls(positions, normals, uvs, indices)
