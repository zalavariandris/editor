from OpenGL.GL import *
import numpy as np

class VBO:
    def __init__(self, data, usage=GL_STATIC_DRAW):
        assert isinstance(data, np.ndarray), "data must be an instance of np.ndarray, got: {}".format(type(data))
        # assert data.dtype == np.float32, "elements must be np.float32, got: {}".format(data.dtype)
        self._handle = glGenBuffers(1)

        #upload data
        glBindBuffer(GL_ARRAY_BUFFER, self._handle)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, usage)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        self._nbytes = data.nbytes
        self._shape = data.shape

    def __enter__(self):
        glBindBuffer(GL_ARRAY_BUFFER, self._handle)

    def __exit__(self, type, value, traceback):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def __del__(self):
        print("delete VBO")
        glDeleteBuffers(1, np.array([self._handle]))

    def get_data(self):
        glBindBuffer(GL_ARRAY_BUFFER, self._handle)
        raw_data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, self._nbytes)
        return np.array(raw_data).view(np.float32).reshape(self._shape)


class EBO:
    def __init__(self, data, usage=GL_STATIC_DRAW):
        self._handle = glGenBuffers(1)

        # upload data to GOU
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._handle)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def __enter__(self):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._handle)

    def __exit__(self, type, value, traceback):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def __del__(self):
        pass

    @property
    def size(self):
        """
        returns the size of the buffer object on the GPU, measured in bytes. 
        The initial value is 0.
        """
        assert self._handle == glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING)
        # TODO: check perfomrance and cache item size
        return glGetBufferParameteriv(GL_ELEMENT_ARRAY_BUFFER , GL_BUFFER_SIZE)

    @property
    def count(self):
        # TODO: check performance and cache item size
        return self.size//np.uint().itemsize
