
from OpenGL.GL import *
import glm
from editor.render.graphics.examples.viewer import Viewer
from editor.render import glsl, puregl, imdraw
from editor.render.graphics import Scene, Mesh, Geometry, Material, PointLight, SpotLight, DirectionalLight
from pathlib import Path

# Create Scene
scene = Scene()
cube = Mesh(geometry=Geometry(*imdraw.geo.sphere()), 
            transform=glm.translate(glm.mat4(1), (0,0.5,0)),
            material=Material(albedo=(1.0,0,0),
                              roughness=0.2,
                              metallic=0.0))
scene.add_child(cube)
plane = Mesh(geometry=Geometry(*imdraw.geo.plane()),
            material=Material(albedo=(0.9,0.9,0.9),
                              roughness=0.7,
                              metallic=0.0))
scene.add_child(plane)
dirlight = DirectionalLight(direction=glm.vec3(1, -6, -2),
                            color=glm.vec3(1.0),
                            intensity=1.0,
                            position=-glm.vec3(1, -6, -2),
                            radius=5,
                            near=1,
                            far=30)
scene.add_child(dirlight)

spotlight = SpotLight(position=glm.vec3(-1, 0.5, -3),
                      direction=glm.vec3(1, -0.5, 3),
                      color=glm.vec3(0.04, 0.6, 1.0),
                      intensity=150.0,
                      fov=60,
                      near=1,
                      far=15)
scene.add_child(spotlight)

pointlight = PointLight(position=glm.vec3(2.5, 1.3, 2.5),
                        color=glm.vec3(1, 0.7, 0.1),
                        intensity=50.0,
                        near=0.1,
                        far=10)
scene.add_child(pointlight)


# Create Viewer
viewer = Viewer(title="Simple PBR with Shadows Example")
@viewer.event
def on_setup():
    global pbr_program
    vert = Path("simple_pbr_with_shadows.vert").read_text()
    frag = Path("simple_pbr_with_shadows.frag").read_text()
    pbr_program = puregl.program.create(vert, frag)

@viewer.event
def on_draw():
    # render each shadowmap:
    for light in scene.lights():
        light.shadowmap.render(scene.meshes(), light.camera)

    # render scene
    glEnable(GL_DEPTH_TEST)
    glCullFace(GL_BACK)
    glViewport(0,0,viewer.width, viewer.height)
    with puregl.program.use(pbr_program) as prog:
        # camera
        puregl.program.set_uniform(prog, "projection", viewer.camera.projection)
        puregl.program.set_uniform(prog, "view", viewer.camera.view)
        puregl.program.set_uniform(prog, "cameraPos", viewer.camera.position)

        # lights
        point_lights = scene.find_all(lambda obj: isinstance(obj, PointLight))
        spot_lights = scene.find_all(lambda obj: isinstance(obj, SpotLight))
        dir_lights = scene.find_all(lambda obj: isinstance(obj, DirectionalLight))
        puregl.program.set_uniform(prog, "num_point_lights", len(point_lights))
        puregl.program.set_uniform(prog, "num_spot_lights", len(spot_lights))
        puregl.program.set_uniform(prog, "num_dir_lights", len(dir_lights))
        active_texture=0
        # set each light uniforms
        for i, light in enumerate(point_lights):
            # light params
            puregl.program.set_uniform(prog, "point_lights[{}].color".format(i), light.color)
            puregl.program.set_uniform(prog, "point_lights[{}].intensity".format(i), light.intensity)
            puregl.program.set_uniform(prog, "point_lights[{}].position".format(i), light.position)

            # shadowmap
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_CUBE_MAP, light.shadowmap.texture)
            puregl.program.set_uniform(prog, "point_lights[{}].shadowCube".format(i), active_texture)
            puregl.program.set_uniform(prog, "point_lights[{}].farPlane".format(i), float(light.far))
            active_texture+=1

        for i, light in enumerate(spot_lights):
            # light params
            puregl.program.set_uniform(prog, "spot_lights[{}].color".format(i), light.color)
            puregl.program.set_uniform(prog, "spot_lights[{}].intensity".format(i), light.intensity)
            puregl.program.set_uniform(prog, "spot_lights[{}].position".format(i), light.position)
            puregl.program.set_uniform(prog, "spot_lights[{}].direction".format(i), light.direction)
            puregl.program.set_uniform(prog, "spot_lights[{}].cutOff".format(i), light.cut_off)

            # shadowmap
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_2D, light.shadowmap.texture)
            puregl.program.set_uniform(prog, "spot_lights[{}].shadowMap".format(i), active_texture)
            puregl.program.set_uniform(prog, "spot_lights[{}].matrix".format(i), light.camera.projection * light.camera.view)
            active_texture+=1

        for i, light in enumerate(dir_lights):
            # light params
            puregl.program.set_uniform(prog, "dir_lights[{}].color".format(i), light.color)
            puregl.program.set_uniform(prog, "dir_lights[{}].intensity".format(i), light.intensity)
            puregl.program.set_uniform(prog, "dir_lights[{}].direction".format(i), light.direction)

            # shadowmap
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_2D, light.shadowmap.texture)
            puregl.program.set_uniform(prog, "dir_lights[{}].shadowMap".format(i), active_texture)
            puregl.program.set_uniform(prog, "dir_lights[{}].matrix".format(i), light.camera.projection * light.camera.view)
            active_texture+=1

        # draw each geometry
        for mesh in scene.meshes():
            puregl.program.set_uniform(prog, "model", mesh.transform)
            puregl.program.set_uniform(prog, "material.albedo", mesh.material.albedo)
            puregl.program.set_uniform(prog, "material.emission", mesh.material.emission)
            puregl.program.set_uniform(prog, "material.roughness", mesh.material.roughness)
            puregl.program.set_uniform(prog, "material.metallic", mesh.material.metallic)
            mesh.geometry._draw(prog)

# Start Main Loop
viewer.start()