import glm
from .cameras import OrthographicCamera, PerspectiveCamera, Camera360

from OpenGL.GL import *
import numpy as np
import logging

from . import Mesh


class DirectionalLight:
    def __init__(self, direction, color, intensity, position, radius, near, far):
        self.direction = direction
        self.color = color
        self.intensity = intensity

        # shadowmap
        self.position = position
        self.radius = radius
        self.near = near
        self.far = far

        self.shadowmap = DepthPass(1024, 1024, cull_face=GL_FRONT)

    @property
    def camera(self):
        tr = glm.lookAt(self.position, self.position+self.direction, (0, 1, 0))
        return OrthographicCamera(glm.inverse(tr), self.radius * 2, self.radius * 2, self.near, self.far) 
    

class SpotLight:
    def __init__(self, position, direction, color, intensity, fov, near, far):
        self.position = position
        self.direction = direction
        self.color = color
        self.intensity = intensity
        self.fov = fov
        self.near = near
        self.far = far

        # self.shadowmap = ShadowMap(1024, 1024, light=self)
        self.shadowmap = DepthPass(1024, 1024, cull_face=GL_FRONT)

    @property
    def camera(self):
        tr = glm.lookAt(self.position, self.position + self.direction, (0, 1, 0))
        return PerspectiveCamera(glm.inverse(tr), self.fov, 1.0, self.near, self.far)

    @property
    def cut_off(self):
        return glm.cos(glm.radians(self.fov / 2))


class PointLight:
    def __init__(self, position, color, intensity, near, far):
        self.position = position
        self.color = color
        self.intensity = intensity
        self.near = near
        self.far = far


        # self.shadowmap = ShadowCubemap(1024, 1024, light=self)
        self.shadowmap = CubeDepthPass(1024, 1024, cull_face=GL_FRONT)

    @property
    def camera(self):
        return Camera360(transform=glm.translate(glm.mat4(1), self.position),
                           near=self.near,
                           far=self.far)
    
 

from .passes import DepthPass, CubeDepthPass
