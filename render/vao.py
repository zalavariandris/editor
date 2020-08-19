from OpenGL.GL import *
import numpy as np
class VAO:
    """
    Vertex Array Object

    Vertex array object stores al of the state needed to supply vertex data.
    It stores the format of the vertex data as well as the Buffer Objects.

    [https://www.khronos.org/opengl/wiki/Vertex_Specification#Vertex_Array_Object]

    """
    def __init__(self):

        # create VAO
        self._handle = glGenVertexArrays(1)
        self._enabled_vertex_attribute_locations = set()

    def set_vertex_attribute(self, location, vbo_handle, size, gtype, normalize=False, stride=0, offset=None):
        glBindBuffer(GL_ARRAY_BUFFER, vbo_handle)
        glVertexAttribPointer(
            location,
            size,
            gtype,
            normalize,
            stride,
            offset
        )
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def enable_vertex_attribute(self, location):
        assert self._handle == glGetIntegerv(GL_VERTEX_ARRAY_BINDING)
        self._enabled_vertex_attribute_locations.add(location)
        glEnableVertexAttribArray(location)

    def disable_vertex_attribute(self, location):
        assert self._handle == glGetIntegerv(GL_VERTEX_ARRAY_BINDING)
        glDisableVertexAttribArray(location)

    def __enter__(self):
        # bind VAO
        glBindVertexArray(self._handle)            
        return self

    def __exit__(self, type, value, traceback):
        for location in self._enabled_vertex_attribute_locations:
            self.disable_vertex_attribute(location)
        # unbind VAO
        assert self._handle == glGetIntegerv(GL_VERTEX_ARRAY_BINDING)
        glBindVertexArray(0)

    def __del__(self):
        # delete VBOs
        # glDeleteBuffers(1, np.array([self.position_vertex_buffer], dtype=np.uint))

        # delete VAO
        glDeleteVertexArrays(1, np.array([self._handle], dtype=np.uint))

