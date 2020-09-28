from editor.render.graphics.passes.renderpass import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl, assets, imdraw

from editor.render.graphics.cameras import Camera360


import numpy as np
from editor.render.graphics.lights import PointLight, DirectionalLight, SpotLight
from editor.render.assets import to_linear


class PBRLightingPass(RenderPass):
    def __init__(self, width, height):
        super().__init__(width, height, seamless_cubemap=True)
        self.texture = None
        self.fbo = None
        self.program = None

    def setup(self):
        super().setup()
        # create program
        # --------------
        self.program = puregl.program.create(*glsl.read("graphics/pbrlighting"))

        with puregl.program.use(self.program):
            puregl.program.set_uniform(self.program, "projectionMatrix", np.eye(4))
            puregl.program.set_uniform(self.program, "viewMatrix", np.eye(4))
            puregl.program.set_uniform(self.program, "modelMatrix", np.eye(4))

        # create textures
        # ---------------
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

        # create depth+stencil buffertarget, pname, param
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def render(self, cameraPos, lights, gBuffer, irradiance, prefilter, brdf):
        super().render()
        gPosition, gNormal, gAlbedo, gEmissive, gRoughness, gMetallic = gBuffer
        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program):
            # clear fbo
            glViewport(0,0, self.width, self.height)
            glClearColor(0.3,0.3,0.3,1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # configure shader
            puregl.program.set_uniform(self.program, "numLights", len(lights))
            puregl.program.set_uniform(self.program, "cameraPos", cameraPos)
            
            glActiveTexture(GL_TEXTURE0+0)
            glBindTexture(GL_TEXTURE_2D, gPosition)
            puregl.program.set_uniform(self.program, "gPosition", 0)

            glActiveTexture(GL_TEXTURE0+1)
            glBindTexture(GL_TEXTURE_2D, gNormal)
            puregl.program.set_uniform(self.program, "gNormal", 1)

            glActiveTexture(GL_TEXTURE0+2)
            glBindTexture(GL_TEXTURE_2D, gAlbedo)
            puregl.program.set_uniform(self.program, "gAlbedoSpecular", 2)

            glActiveTexture(GL_TEXTURE0+3)
            glBindTexture(GL_TEXTURE_2D, gRoughness)
            puregl.program.set_uniform(self.program, "gRoughness", 3)

            glActiveTexture(GL_TEXTURE0+4)
            glBindTexture(GL_TEXTURE_2D, gMetallic)
            puregl.program.set_uniform(self.program, "gMetallic", 4)

            glActiveTexture(GL_TEXTURE0+5)
            glBindTexture(GL_TEXTURE_2D, gEmissive)
            puregl.program.set_uniform(self.program, "gEmissive", 5)

            glActiveTexture(GL_TEXTURE0+6)
            glBindTexture(GL_TEXTURE_CUBE_MAP, irradiance)
            puregl.program.set_uniform(self.program, "irradianceMap", 6)

            glActiveTexture(GL_TEXTURE0+7)
            glBindTexture(GL_TEXTURE_CUBE_MAP, prefilter)
            puregl.program.set_uniform(self.program, "prefilterMap", 7)

            glActiveTexture(GL_TEXTURE0+8)
            glBindTexture(GL_TEXTURE_2D, brdf)
            puregl.program.set_uniform(self.program, "brdfLUT", 8)

            shadowMapIdx, shadowCubeIdx = 0, 0
            for i, light in enumerate(lights):
                slot = 9+i
                if isinstance(light, DirectionalLight):
                    puregl.program.set_uniform(self.program, "lights[{}].type".format(i), 0)
                    puregl.program.set_uniform(self.program, "lights[{}].color".format(i), to_linear(light.color)*light.intensity)

                    puregl.program.set_uniform(self.program, "lights[{}].direction".format(i), light.direction)
                    puregl.program.set_uniform(self.program, "lights[{}].shadowIdx".format(i), shadowMapIdx)
                    
                    glActiveTexture(GL_TEXTURE0+slot)
                    glBindTexture(GL_TEXTURE_2D, light.shadowmap.texture)
                    puregl.program.set_uniform(self.program, "lights[{}].matrix".format(i), light.camera.projection * light.camera.view)
                    puregl.program.set_uniform(self.program, "shadowMaps[{}]".format(shadowMapIdx), slot)
                    shadowMapIdx += 1

                elif isinstance(light, SpotLight):
                    puregl.program.set_uniform(self.program, "lights[{}].type".format(i), 1)
                    puregl.program.set_uniform(self.program, "lights[{}].color".format(i), to_linear(light.color)*light.intensity)

                    puregl.program.set_uniform(self.program, "lights[{}].position".format(i), light.position)
                    puregl.program.set_uniform(self.program, "lights[{}].direction".format(i), light.direction)
                    puregl.program.set_uniform(self.program, "lights[{}].cutOff".format(i), light.cut_off)

                    glActiveTexture(GL_TEXTURE0+slot)
                    glBindTexture(GL_TEXTURE_2D, light.shadowmap.texture)
                    puregl.program.set_uniform(self.program, "lights[{}].matrix".format(i), light.camera.projection * light.camera.view)
                    puregl.program.set_uniform(self.program, "lights[{}].shadowIdx".format(i), shadowMapIdx)
                    puregl.program.set_uniform(self.program, "shadowMaps[{}]".format(shadowMapIdx), slot)
                    shadowMapIdx += 1

                elif isinstance(light, PointLight):
                    puregl.program.set_uniform(self.program, "lights[{}].type".format(i), 2)
                    puregl.program.set_uniform(self.program, "lights[{}].color".format(i), to_linear(light.color)*light.intensity)
                    puregl.program.set_uniform(self.program, "lights[{}].position".format(i), light.position)

                    glActiveTexture(GL_TEXTURE0+slot)
                    glBindTexture(GL_TEXTURE_CUBE_MAP, light.shadowmap.texture)
                    puregl.program.set_uniform(self.program, "lights[{}].farPlane".format(i), float(light.far))
                    puregl.program.set_uniform(self.program, "lights[{}].shadowIdx".format(i), shadowCubeIdx)
                    puregl.program.set_uniform(self.program, "shadowCubes[{}]".format(shadowCubeIdx), slot)
                    shadowCubeIdx += 1

            # draw
            imdraw.quad(self.program)
        return self.texture


if __name__ == "__main__":
    from editor.render.graphics.passes import GeometryPass
    from editor.render.graphics.passes import EnvironmentPass
    from editor.render.graphics.passes import IrradiancePass, PrefilterPass, BRDFPass
    import glm
    from editor.render.graphics import Scene, Mesh, Geometry, Material

    from editor.render.graphics.examples.viewer import Viewer

    viewer = Viewer()

    # assets
    environment_image = assets.imread('hdri/Tropical_Beach_3k.hdr').astype(np.float32)

    # scene
    scene = Scene()
    scene.add_child(Mesh(transform=glm.translate(glm.mat4(1), (0.0,0.5, 0.0)),
                         geometry=Geometry(*imdraw.geo.sphere()),
                         material=Material(albedo=glm.vec3(0.5),
                                           emission=(0,0,0),
                                           roughness=glm.pow(0.5, 2),
                                           metallic=0.0)))
    scene.add_child(Mesh(geometry=Geometry(*imdraw.geo.plane())))

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
                            intensity=17.5,
                            near=0.1,
                            far=10)
    scene.add_child(pointlight)

    # init passes
    geometry_pass = GeometryPass(viewer.width, viewer.height)
    environment_pass = EnvironmentPass(512,512)
    irradiance_pass = IrradiancePass(32,32)
    prefilter_pass = PrefilterPass(128,128)
    brdf_pass = BRDFPass(512, 512)
    lighting_pass = PBRLightingPass(viewer.width, viewer.height)

    @viewer.event
    def on_setup():
        global environment_texture
        environment_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, environment_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, environment_image.shape[1], environment_image.shape[0], 
            0, GL_RGB, GL_FLOAT, environment_image)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D,0)

        # render passes
        global environment_cubemap, irradiance_cubemap, prefilter_cubemap, brdf_texture
        camera360 = Camera360(transform=glm.mat4(1), near=0.1, far=15)
        environment_cubemap = environment_pass.render(environment_texture, camera360)
        irradiance_cubemap = irradiance_pass.render(environment_cubemap, camera360)
        prefilter_cubemap = prefilter_pass.render(environment_cubemap, camera360)
        brdf_texture = brdf_pass.render()

    @viewer.event
    def on_draw():
        # geometry ass
        gBuffer = geometry_pass.render(scene.find_meshes(), viewer.camera)

        # shadows pass
        for light in scene.find_lights():
            light.shadowmap.render(scene.find_meshes(), light.camera)

        # lighting pass
        hdr_texture = lighting_pass.render(viewer.camera.position, scene.find_lights(), gBuffer, irradiance_cubemap, prefilter_cubemap, brdf_texture)

        # Debug
        # -----
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

        # debug beauty
        imdraw.texture(hdr_texture,  (  0,0,viewer.width, viewer.height), shuffle=(0,1,2,-1))

        # debug shadows
        for i, light in enumerate( scene.find_lights() ):
            if isinstance(light, PointLight):
                imdraw.cubemap(light.shadowmap.texture, (i*100, 200, 90, 90), viewer.camera.projection, viewer.camera.view, shuffle=(0,0,0,-1))
            elif isinstance(light, (SpotLight, DirectionalLight)):
                imdraw.texture(light.shadowmap.texture, (i*100, 200, 90, 90), shuffle=(0,0,0,-1))

        # debug gBuffer
        gPosition, gNormal, gAlbedo, gEmissive, gRoughness, gMetallic = gBuffer
        imdraw.texture(gPosition,  (  0,0,90, 90), shuffle=(0,1,2,-1))
        imdraw.texture(gNormal,    (100,0,90, 90), shuffle=(0,1,2,-1))
        imdraw.texture(gAlbedo,    (200,0,90, 90), shuffle=(0,1,2,-1))
        imdraw.texture(gEmissive,  (300,0,90, 90))
        imdraw.texture(gRoughness, (400,0,90, 90), shuffle=(0,0,0,-1))
        imdraw.texture(gMetallic,  (500,0,90, 90), shuffle=(0,0,0,-1))

        # debug IBL      
        imdraw.texture(environment_texture, (  0, 100, 90, 90))
        imdraw.cubemap(environment_cubemap, (100, 100, 90, 90), viewer.camera.projection, viewer.camera.view)
        imdraw.cubemap(irradiance_cubemap,  (200, 100, 90, 90), viewer.camera.projection, viewer.camera.view)
        imdraw.cubemap(prefilter_cubemap,   (300, 100, 90, 90), viewer.camera.projection, viewer.camera.view)
        imdraw.texture(brdf_texture,        (400, 100, 90, 90))

    viewer.start()
    print("- end of program -")
