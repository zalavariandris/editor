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
        scene = Scene()
        for j in range(2):
            for i in range(5):
                sphere = Mesh(transform=glm.translate(glm.mat4(1), (i*1.0-2.5,0.5, j*3-1.5)),
                              geometry=Geometry(*puregl.geo.sphere()),
                              material=Material(albedo=glm.vec3(0.5),
                                                emission=(0,0,0),
                                                roughness=i/8.0,
                                                metallic=float(j)))
                print(j)
                scene.add_child(sphere)


        # cube = Mesh(transform=glm.translate(glm.mat4(1), (1.0, 0.5, 0.0)) * glm.rotate(glm.mat4(1), glm.radians(30), (0,1,0)),
        #         geometry=Geometry(*puregl.geo.cube()),
        #         material=Material(albedo=(1, 0, 0),
        #                           emission=(0,0,0),
        #                           roughness=0.7,
        #                           metallic=0.0))
        # scene.add_child(cube)

        # plane = Mesh(transform=glm.translate(glm.mat4(1), (0, 0.0, 0.0)),
        #              geometry=Geometry(*puregl.geo.plane()),
        #              material=Material(albedo=(0.5, 0.5, 0.5),
        #                                emission=(0,0,0),
        #                                roughness=0.8,
        #                                metallic=0.0))
        # scene.add_child(plane)
        
        return scene

