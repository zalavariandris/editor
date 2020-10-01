from editor.render.graphics.passes import RenderPass
from editor.render.graphics.passes import EnvironmentPass
from editor.render.graphics.passes import IrradiancePass, PrefilterPass, BRDFPass
from editor.render.graphics import Scene, Mesh, PerspectiveCamera, OrthographicCamera, Camera360
from editor.render import assets
from editor.render.graphics.passes import RenderPass
from editor.render import glsl, puregl, imdraw
from OpenGL.GL import *

# DeferredRenderer
# - precompute
#   - environment cubemap
#   - irradiance map
#   - prefilter map
#   - brdf map
# - each_frame:
#   - GeometryPass
#   - Prerender textures:
#     - render light shadowmaps
#   - LightingPass

# ForwardRenderer
# - copydepth_from_geometry_pass
# - render each transparent, and special material objects

# PostProcess
# - gamma correction and tonemapping
# - clamp blur ldr clamped
# - ldr add clamped
# - display beauty texture

# DEFERRED 
# ========
class GeometryPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, depth_test=True, cull_face=GL_BACK, blending=False)

        self.gPosition = self.gNormal = self.gAlbedo = self.gEmission = self.gRoughness = self.gMetallic = None
        self.fbo = None
        self.program = None

    def setup(self):
        super().setup()
        # Create textures
        # ---------------
        self.gPosition, self.gNormal, self.gAlbedo, self.gEmission, self.gRoughness, self.gMetallic = glGenTextures(6)
        
        # define textures
        glBindTexture(GL_TEXTURE_2D, self.gPosition)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gNormal)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gAlbedo)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gEmission)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gRoughness)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, self.width, self.height, 0, GL_RED, GL_FLOAT, None)

        glBindTexture(GL_TEXTURE_2D, self.gMetallic)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, self.width, self.height, 0, GL_RED, GL_FLOAT, None)
        
        # configure textures
        for tex in [self.gPosition, self.gNormal, self.gAlbedo, self.gEmission, self.gRoughness, self.gMetallic]:
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)

        # create render buffer
        self.gDepth = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.gDepth)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, self.width, self.height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

        # Create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)

        # configure fbo
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffers(6, [GL_COLOR_ATTACHMENT0+i for i in range(6)])

        # attach textures
        for i, tex in enumerate([self.gPosition, self.gNormal, self.gAlbedo, self.gEmission, self.gRoughness, self.gMetallic]):
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+i, GL_TEXTURE_2D, tex, 0
            )

        # attach render buffers
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.gDepth, 0
        )

        # cleanup
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Create program
        # --------------
        self.program = puregl.program.create(*glsl.read("graphics/geometry"))

    def render(self, objects: [Mesh], camera: (PerspectiveCamera, OrthographicCamera)):
        super().render()

        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program):
            glViewport(0,0, self.width, self.height)
            glClearColor(0,0,0,0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # set camera
            puregl.program.set_uniform(self.program, "projection", camera.projection)
            puregl.program.set_uniform(self.program, "view", camera.view)

            # draw scene
            for mesh in objects:
                # transform
                puregl.program.set_uniform(self.program, "model", mesh.transform)

                # material
                puregl.program.set_uniform(self.program, "albedo", assets.to_linear(glm.vec3(*mesh.material.albedo)))
                puregl.program.set_uniform(self.program, "emission", assets.to_linear(glm.vec3(*mesh.material.emission)))
                puregl.program.set_uniform(self.program, "roughness", mesh.material.roughness)
                puregl.program.set_uniform(self.program, "metallic", mesh.material.metallic)

                # geometry
                mesh.geometry._draw(self.program)

        return self.gPosition, self.gNormal, self.gAlbedo, self.gEmission, self.gRoughness, self.gMetallic

class PBRLightingPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, seamless_cubemap=True)
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


    def render(self, gBuffer, iblBuffer, cameraPos, lights):
        super().render()
        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program) as prog:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            # camera
            puregl.program.set_uniform(prog, "projection", glm.mat4(1))
            puregl.program.set_uniform(prog, "view", glm.mat4(1))
            puregl.program.set_uniform(prog, "cameraPos", cameraPos)

            # lights
            point_lights = [light for light in lights if isinstance(light, PointLight)]
            spot_lights =  [light for light in lights if isinstance(light, SpotLight)]
            dir_lights =   [light for light in lights if isinstance(light, DirectionalLight)]
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

            # Set Geometry Buffer
            gPosition, gNormal, gAlbedo, gEmission, gRoughness, gMetallic = gBuffer
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_2D, gPosition)
            puregl.program.set_uniform(prog, "gPosition", active_texture)
            active_texture+=1
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_2D, gNormal)
            puregl.program.set_uniform(prog, "gNormal", active_texture)
            active_texture+=1
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_2D, gEmission)
            puregl.program.set_uniform(prog, "gAlbedo", active_texture)
            active_texture+=1
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_2D, gEmission)
            puregl.program.set_uniform(prog, "gEmission", active_texture)
            active_texture+=1
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_2D, gRoughness)
            puregl.program.set_uniform(prog, "gRoughness", active_texture)
            active_texture+=1
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_2D, gMetallic)
            puregl.program.set_uniform(prog, "gMetallic", active_texture)
            active_texture+=1

            # set IBL buffers
            irradianceMap, prefilterMap, brdfLUT = iblBuffer
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_CUBE_MAP, irradianceMap)
            puregl.program.set_uniform(prog, "irradianceMap", active_texture)
            active_texture+=1
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_CUBE_MAP, prefilterMap)
            puregl.program.set_uniform(prog, "prefilterMap", active_texture)
            active_texture+=1
            glActiveTexture(GL_TEXTURE0+active_texture)
            glBindTexture(GL_TEXTURE_2D, brdfLUT)
            puregl.program.set_uniform(prog, "brdfLUT", active_texture)
            active_texture+=1


            # draw quad
            puregl.program.set_uniform(prog, "model", glm.mat4(1))
            imdraw.quad(prog)

            # # draw each geometry
            # for mesh in scene.meshes():
            #     puregl.program.set_uniform(prog, "model", mesh.transform)
            #     puregl.program.set_uniform(prog, "material.albedo", mesh.material.albedo)
            #     puregl.program.set_uniform(prog, "material.emission", mesh.material.emission)
            #     puregl.program.set_uniform(prog, "material.roughness", mesh.material.roughness)
            #     puregl.program.set_uniform(prog, "material.metallic", mesh.material.metallic)
            #     mesh.geometry._draw(prog)

        return self.texture

# FORWARD
# =======
# forward rendering skybox
class SkyboxPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, True, GL_BACK)
        self.program = None
        self.texture = None
        self.fbo = None

    def setup(self):
        super().setup()
        # create program
        self.program = puregl.program.create(*glsl.read('skybox'))

        # create texture
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.width, self.height, 0, GL_RGB, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

        # create fbo
        self.fbo = glGenFramebuffers(1)
        with puregl.fbo.bind(self.fbo):
            glDrawBuffers(1, [GL_COLOR_ATTACHMENT0 + 0])
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0
            )

            # create depth+stencil buffer
            rbo = glGenRenderbuffers(1)
            glBindRenderbuffer(GL_RENDERBUFFER, rbo)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
            glBindRenderbuffer(GL_RENDERBUFFER, 0)

            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
            assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

    def render(self, environment, camera):
        super().render()
        with puregl.fbo.bind(self.fbo):
            # draw skybox
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LEQUAL)
            glDepthMask(GL_FALSE)
            glViewport(0, 0, self.width, self.height)
            with puregl.program.use(self.program) as prog:
                puregl.program.set_uniform(prog, 'projection', camera.projection)
                sky_view = glm.mat4(glm.mat3(camera.view));
                puregl.program.set_uniform(prog, 'view', sky_view)
                puregl.program.set_uniform(prog, 'cameraPos', camera.position)
                puregl.program.set_uniform(prog, 'skybox', 0)
                puregl.program.set_uniform(prog, 'groundProjection', True)
                glActiveTexture(GL_TEXTURE0 + 0)
                glBindTexture(GL_TEXTURE_CUBE_MAP, environment)
                imdraw.cube(prog, flip=True)

                glBindTexture(GL_TEXTURE_CUBE_MAP, 0)
            glDepthMask(GL_TRUE)
        return self.texture

# POST PROCESS
# ============
class PostprocessPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height)

    def setup(self):
        super().setup()

    def render(self, input_texture):
        super().render()
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

    environment_image = assets.imread("hdri/Tropical_Beach_3k.hdr")

    # Create Viewer
    viewer = Viewer(title="Simple PBR with Shadows Example")

    # Create render pipeline
    geometry_pass = GeometryPass(viewer.width, viewer.height)
    environment_pass = EnvironmentPass(512, 512)
    irradiance_pass = IrradiancePass(32,32)
    prefilter_pass = PrefilterPass(128,128)
    brdf_pass = BRDFPass(512, 512)
    lighting_pass = PBRLightingPass(viewer.width, viewer.height)
    skybox_pass = SkyboxPass(viewer.width, viewer.height)

    @viewer.event
    def on_setup():
        global environment_texture
        environment_texture = glGenTextures(1)
        h, w, c = environment_image.shape
        glBindTexture(GL_TEXTURE_2D, environment_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, w, h, 0, GL_RGB, GL_FLOAT, environment_image)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

        global environment_cubemap, irradiance_cubemap, prefilter_cubemap, brdfLUT
        camera360 = Camera360(transform=glm.mat4(1), near=0.1, far=15)
        environment_cubemap = environment_pass.render(environment_texture, camera360)
        irradiance_cubemap = irradiance_pass.render(environment_cubemap, camera360)
        prefilter_cubemap = prefilter_pass.render(environment_cubemap, camera360)
        brdfLUT = brdf_pass.render()

    @viewer.event
    def on_draw():
        # PREPROCESS
        # - render each shadowmap:
        for light in scene.lights():
            light.shadowmap.render(scene.meshes(), light.camera)


        # DEFERRED
        # - render geometry pass
        gBuffer = geometry_pass.render(scene.meshes(), viewer.camera)

        # - render pbr lighting
        iblBuffer = irradiance_cubemap, prefilter_cubemap, brdfLUT
        hdr_image = lighting_pass.render(gBuffer, iblBuffer, viewer.camera.position, scene.lights())

        # FORWARD
        # - copy fbo depth and color
        skybox_pass.copy_buffer_from(geometry_pass, GL_DEPTH_BUFFER_BIT)
        skybox_pass.copy_buffer_from(lighting_pass, GL_COLOR_BUFFER_BIT)
        # - render skybox
        skybox_texture = skybox_pass.render(environment_cubemap, viewer.camera)

        # POST PROCESS


        # DEBUG
        glDisable(GL_DEPTH_TEST)
        imdraw.texture(skybox_texture, (0,0,viewer.width, viewer.height))
        
        # - debug gBuffer
        gPosition, gNormal, gAlbedo, gEmissive, gRoughness, gMetallic = gBuffer
        imdraw.texture(gPosition,  (  0,0,90, 90), shuffle=(0,1,2,-1))
        imdraw.texture(gNormal,    (100,0,90, 90), shuffle=(0,1,2,-1))
        imdraw.texture(gAlbedo,    (200,0,90, 90), shuffle=(0,1,2,-1))
        imdraw.texture(gEmissive,  (300,0,90, 90))
        imdraw.texture(gRoughness, (400,0,90, 90), shuffle=(0,0,0,-1))
        imdraw.texture(gMetallic,  (500,0,90, 90), shuffle=(0,0,0,-1))

        # - debug IBL      
        imdraw.texture(environment_texture, (  0, 100, 90, 90))
        imdraw.cubemap(environment_cubemap, (100, 100, 90, 90), viewer.camera.projection, viewer.camera.view)
        imdraw.cubemap(irradiance_cubemap,  (200, 100, 90, 90), viewer.camera.projection, viewer.camera.view)
        imdraw.cubemap(prefilter_cubemap,   (300, 100, 90, 90), viewer.camera.projection, viewer.camera.view)
        imdraw.texture(brdfLUT,        (400, 100, 90, 90))

    # Start Main Loop
    viewer.start()

    @viewer.event
    def on_draw():
        render_skybox()