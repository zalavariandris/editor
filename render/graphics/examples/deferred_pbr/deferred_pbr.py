from editor.render.graphics.passes import RenderPass

class PBRLightingPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, True, GL_BACK, False, False)
        self.program = None
        self.fbo = None
        self.texture = None

    def setup(self):
        super().setup()
        # create program
        # --------------
        vert = Path("deferred_pbr_lighting.vert").read_text()
        frag = Path("deferred_pbr_lighting.frag").read_text()
        self.program = puregl.program.create(vert, frag)

        # create texture(s)
        # ----------------
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)

        # create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffers(1, [GL_COLOR_ATTACHMENT0+0])
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+0, GL_TEXTURE_2D, self.texture, 0
        )
        glBindTexture(GL_TEXTURE_2D, 0)

        # create render buffers for depth and stencil
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def render(self, scene, camera):
        super().render()
        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program) as prog:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            # camera
            puregl.program.set_uniform(prog, "projection", camera.projection)
            puregl.program.set_uniform(prog, "view", camera.view)
            puregl.program.set_uniform(prog, "cameraPos", camera.position)

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

        return self.texture

if __name__ == "__main__":
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

    # Create render pipeline
    pbrpass = PBRLightingPass(viewer.width, viewer.height)

    @viewer.event
    def on_setup():
        global pbr_program
        vert = Path("deferred_pbr_lighting.vert").read_text()
        frag = Path("deferred_pbr_lighting.frag").read_text()
        pbr_program = puregl.program.create(vert, frag)

    @viewer.event
    def on_draw():
        # render each shadowmap:
        for light in scene.lights():
            light.shadowmap.render(scene.meshes(), light.camera)

        # render geometry pass
        geometry = geometrypass.render(scene, viewer.camera)

        # render pbr lighting
        ldr_image = pbrpass.render(scene, viewer.camera)
        imdraw.texture(ldr_image, (0,0,viewer.width,viewer.height))
    # Start Main Loop
    viewer.start()