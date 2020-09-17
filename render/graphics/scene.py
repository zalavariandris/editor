from . import Mesh, Geometry, Material
import glm
from editor.render import puregl

class Scene:
    def __init__(self, children=[]):
        self._children = children

    def add_child(self, child: Mesh) -> None:
        assert isinstance(child, Mesh)
        self._children.append(child)

    @property
    def children(self) -> [Mesh]:
        return self._children

    def _setup(self):
        for child in self._children:
            child.geometry._setup()

    @staticmethod
    def test_scene():
        cube = Mesh(transform=glm.translate(glm.mat4(1), (1, 0.5, 0.0)),
                    geometry=Geometry(*puregl.geo.cube()),
                    material=Material(albedo=(1, 0, 0),
                                      roughness=0.7,
                                      metallic=0.0))
        sphere = Mesh(transform=glm.translate(glm.mat4(1), (-1,0.5, 0.0)),
                      geometry=Geometry(*puregl.geo.sphere()),
                      material=Material(albedo=(0.04, 0.5, 0.8),
                                        roughness=0.2,
                                        metallic=1.0))
        plane = Mesh(transform=glm.translate(glm.mat4(1), (0, 0.0, 0.0)),
                     geometry=Geometry(*puregl.geo.plane()),
                     material=Material(albedo=(0.5, 0.5, 0.5),
                                       roughness=0.8,
                                       metallic=0.0))

        scene = Scene()
        scene.add_child(cube)
        scene.add_child(sphere)
        scene.add_child(plane)

        return scene

