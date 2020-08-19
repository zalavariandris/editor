from OpenGL.GL import *
import numpy as np

class Texture:
    def __init__(self, data, texture_unit):
        """
        slot: bind tio texture unit
        """
        assert isinstance(data, np.ndarray), "data must be an instance of np.ndarray, got: {}".format(type(data))
        assert data.dtype == np.float32, "elements must be np.float32, got: {}".format(data.dtype)
       
        self._handle = glGenTextures(1)
        self.texture_unit = texture_unit
        glActiveTexture(GL_TEXTURE0+self.texture_unit)
        glBindTexture(GL_TEXTURE_2D, self._handle)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 64, 64, 0, GL_BGR, GL_FLOAT, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)

    def bind(self, texture_unit):
        """slot: bind tio texture unit"""
        self.texture_unit = texture_unit
        glActiveTexture(GL_TEXTURE0+self.texture_unit)
        glBindTexture(GL_TEXTURE_2D, self._handle)

    def unbind(self):
        glBindTexture(GL_TEXTURE_2D, 0)

    def __call__(self, texture_unit):
        self.texture_unit = texture_unit
        return self

    def __enter__(self):
        self.bind(self.texture_unit)

    def __exit__(self, type, value, traceback):
        self.unbind()

    def __del__(self):
        pass