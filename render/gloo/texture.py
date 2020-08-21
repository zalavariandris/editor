from OpenGL.GL import *
import numpy as np

class Texture:
    def __init__(self, slot):
        """
        slot: bind to texture unit
        """
        self._handle = glGenTextures(1)
        self.texture_unit = slot

    @classmethod
    def from_data(cls, data, slot):
        assert isinstance(data, np.ndarray)
        assert data.shape[2] is 3, "got: {}".format(data.shape[2])
        obj = cls(slot)
        height, width, channels = data.shape
        glActiveTexture(GL_TEXTURE0+obj.texture_unit)
        glBindTexture(GL_TEXTURE_2D, obj._handle)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_BGR, GL_FLOAT, data)
        glBindTexture(GL_TEXTURE_2D, 0)
        return obj

    @classmethod
    def from_size(cls, size, slot):
        obj = cls(slot)
        height, width = size
        glActiveTexture(GL_TEXTURE0+obj.texture_unit)
        glBindTexture(GL_TEXTURE_2D, obj._handle)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_BGR, GL_FLOAT, None)
        glBindTexture(GL_TEXTURE_2D, 0)
        return obj

    def bind(self, slot=None):
        """slot: bind tio texture unit"""
        if slot:
            self.texture_unit = slot
        glActiveTexture(GL_TEXTURE0+self.texture_unit)
        glBindTexture(GL_TEXTURE_2D, self._handle)

    def unbind(self):
        glBindTexture(GL_TEXTURE_2D, 0)

    def __call__(self, slot):
        self.texture_unit = slot
        return self

    def __enter__(self):
        self.bind(self.texture_unit)

    def __exit__(self, type, value, traceback):
        self.unbind()

    def __del__(self):
        pass