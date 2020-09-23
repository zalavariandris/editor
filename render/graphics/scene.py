from . import Mesh, Geometry, Material
import glm
from editor.render import puregl
import numpy as np


class Scene:
    def __init__(self, children=[]):
        self._children = children

    def add_child(self, child: Mesh) -> None:
        self._children.append(child)

    def setup(self):
        from . import Mesh
        for geometry in {mesh.geometry for mesh in self.find_all(lambda obj: isinstance(obj, Mesh))}:
            geometry._setup()

        from .lights import PointLight, SpotLight, DirectionalLight
        lights = self.find_all(lambda obj: isinstance(obj, (PointLight, SpotLight, DirectionalLight)))
        for light in lights:
            light._setup_shadows()

    @property
    def children(self) -> [Mesh]:
        return self._children

    def find_all(self, predicate):
        return [child for child in self._children if predicate(child)]

    def find_meshes(self):
        return self.find_all(lambda obj: isinstance(obj, Mesh))

    def find_lights(self):
        from .lights import PointLight, SpotLight, DirectionalLight
        return self.find_all(lambda obj: isinstance(obj, (PointLight, SpotLight, DirectionalLight)))

    @staticmethod
    def test_scene():
        from .lights import PointLight, SpotLight, DirectionalLight
        scene = Scene()
        for j in range(2):
            for x, roughness in zip(np.linspace(-3,3, 5), np.linspace(0,1, 5)):
                sphere = Mesh(transform=glm.translate(glm.mat4(1), (x,0.5, j*3-1.5)),
                              geometry=Geometry(*puregl.geo.sphere()),
                              material=Material(albedo=glm.vec3(0.5),
                                                emission=(0,0,0),
                                                roughness=roughness,
                                                metallic=float(j)))
                print(j)
                scene.add_child(sphere)

        dirlight = DirectionalLight(direction=glm.vec3(1, -6, -2),
                                    color=glm.vec3(1.0),
                                    intensity=1.0,
                                    position=-glm.vec3(1, -6, -2),
                                    radius=5,
                                    near=1,
                                    far=30)

        spotlight = SpotLight(position=glm.vec3(-1, 0.5, -3),
                              direction=glm.vec3(1, -0.5, 3),
                              color=glm.vec3(0.04, 0.6, 1.0),
                              intensity=150.0,
                              fov=60,
                              near=1,
                              far=15)

        pointlight = PointLight(position=glm.vec3(2.5, 1.3, 2.5),
                                color=glm.vec3(1, 0.7, 0.1),
                                intensity=17.5,
                                near=0.1,
                                far=10)

        scene.add_child(dirlight)
        scene.add_child(spotlight)
        scene.add_child(pointlight)


        # cube = Mesh(transform=glm.translate(glm.mat4(1), (1.0, 0.5, 0.0)) * glm.rotate(glm.mat4(1), glm.radians(30), (0,1,0)),
        #         geometry=Geometry(*puregl.geo.cube()),
        #         material=Material(albedo=(1, 0, 0),
        #                           emission=(0,0,0),
        #                           roughness=0.7,
        #                           metallic=0.0))
        # scene.add_child(cube)

        plane = Mesh(transform=glm.translate(glm.mat4(1), (0, 0.0, 0.0)),
                     geometry=Geometry(*puregl.geo.plane()),
                     material=Material(albedo=(0.5, 0.5, 0.5),
                                       emission=(0,0,0),
                                       roughness=0.8,
                                       metallic=0.0))
        scene.add_child(plane)
        
        return scene

    @staticmethod
    def from_trimesh_scene(triscene):
        import uuid
        import logging
        from editor.render.graphics import Scene, Mesh, Geometry, Material
        # read scene

        scene = Scene()
        # convert gltf
        for name, data in triscene.graph.transforms.nodes(data=True):
            # extract transform
            import glm
            transform = glm.mat4(triscene.graph[name][0])

            # extract mesh
            hasGeometry = 'geometry' in data
            if hasGeometry:
                trigeo = triscene.geometry[data['geometry']]
                print("!!!!!!!!!!", name)
                print(transform)
                # geometry
                geometry = Geometry(positions = trigeo.vertices.astype(np.float32),
                            indices =   trigeo.faces.astype(np.uint),
                            normals =   trigeo.vertex_normals.astype(np.float32),
                            uvs =       trigeo.visual.uv.astype(np.float32))

                # material
                print("!!!!!!!!!!", trigeo.visual.material.baseColorFactor)
                material = Material(albedo=glm.vec3(*trigeo.visual.material.baseColorFactor[:3]/255),
                            emission=trigeo.visual.material.emissiveFactor[:3]/255,
                            roughness=float(trigeo.visual.material.roughnessFactor),
                            metallic=float(trigeo.visual.material.metallicFactor))

                scene.add_child(Mesh(name=name,
                                    transform=glm.transpose(transform),
                                    geometry=geometry,
                                    material=material))
            else:
                logging.warning("currently only supports mesh")
            # extract light

        return scene

    def plot(self):
        for obj in self.children:
            print("•",obj.name)



