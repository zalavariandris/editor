import glm
from .cameras import OrthographicCamera, PerspectiveCamera, Camera360
from .passes import DepthPass, CubeDepthPass
from OpenGL.GL import *
import numpy as np


class DirectionalLight:
    def __init__(self, direction, color, position, radius, near, far):
        self.direction = direction
        self.color = color
        self.position = position
        self.radius = radius
        self.near = near
        self.far = far

        self._shadow_pass = DepthPass(1024, 1024, cull_face=GL_FRONT)
        self._depth_map = None

    @property
    def projection(self):
        return glm.ortho(-5, 5, -5, 5, self.near, self.far)

    @property
    def view(self):
        return glm.lookAt(self.position, self.position + self.direction, (0, 1, 0))

    @property
    def camera(self):
        tr = glm.lookAt(self.position, self.position + self.direction, (0, 1, 0))
        return OrthographicCamera(glm.inverse(tr), self.radius * 2, self.radius * 2, self.near, self.far)

    def _setup_shadows(self):
        """setup shadows"""
        self._shadow_pass.setup()

    def _render_shadows(self, scene):
        """render shadows"""
        self._shadow_map = self._shadow_pass.render(scene, self.camera)


class Spotlight:
    def __init__(self, position, direction, color, fov, near, far):
        self.position = position
        self.direction = direction
        self.color = color
        self.fov = fov
        self.near = near
        self.far = far

        self._shadow_pass = DepthPass(1024, 1024, cull_face=GL_FRONT)
        self._depth_map = None

    @property
    def cut_off(self):
        return glm.cos(glm.radians(self.fov / 2))

    @property
    def projection(self):
        aspect = 1.0
        return glm.perspective(glm.radians(self.fov), aspect, self.near, self.far)

    @property
    def view(self):
        return glm.lookAt(self.position, self.position + self.direction, (0, 1, 0))

    @property
    def camera(self):
        tr = glm.lookAt(self.position, self.position + self.direction, (0, 1, 0))
        return PerspectiveCamera(glm.inverse(tr), self.fov, 1.0, self.near, self.far)

    def _setup_shadows(self):
        """setup shadows"""
        self._shadow_pass.setup()

    def _render_shadows(self, scene):
        """render shadows"""
        self._shadow_map = self._shadow_pass.render(scene, self.camera)


class Pointlight:
    def __init__(self, position, color, near, far):
        self.position = position
        self.color = color
        self.near = near
        self.far = far

        self._shadow_pass = CubeDepthPass(1024, 1024, cull_face=GL_FRONT)
        self._depth_map = None

    @property
    def projection(self):
        aspect = 1.0
        return glm.perspective(glm.radians(90.0), aspect, self.near, self.far)

    @property
    def views(self):
        matrices = []
        matrices.append(
            glm.lookAt(self.position, self.position + glm.vec3(1, 0, 0), glm.vec3(0, -1, 0)))
        matrices.append(
            glm.lookAt(self.position, self.position + glm.vec3(-1, 0, 0), glm.vec3(0, -1, 0)))
        matrices.append(
            glm.lookAt(self.position, self.position + glm.vec3(0, 1, 0), glm.vec3(0, 0, 1)))
        matrices.append(
            glm.lookAt(self.position, self.position + glm.vec3(0, -1, 0), glm.vec3(0, 0, -1)))
        matrices.append(
            glm.lookAt(self.position, self.position + glm.vec3(0, 0, 1), glm.vec3(0, -1, 0)))
        matrices.append(
            glm.lookAt(self.position, self.position + glm.vec3(0, 0, -1), glm.vec3(0, -1, 0)))

        return np.array([np.array(m) for m in matrices])

    @property
    def camera(self):
        return Camera360(transform=glm.translate(glm.mat4(1), self.position),
                         near=self.near,
                         far=self.far)

    def _setup_shadows(self):
        """setup shadows"""
        self._shadow_pass.setup()

    def _render_shadows(self, scene):
        """render shadows"""
        self._shadow_map = self._shadow_pass.render(scene, self.camera)
