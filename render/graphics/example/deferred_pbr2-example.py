from editor.render.graphics.passes.renderpass import RenderPass
from OpenGL.GL import *
from editor.render import puregl, glsl, assets
from editor.render.graphics import Scene
from editor.render.graphics.cameras import Camera360
from editor.render.graphics.lights import Spotlight, Pointlight, DirectionalLight
import numpy as np
import glm

from editor.render.graphics.passes import GeometryPass, EnvironmentPass
from editor.render.graphics.passes import IrradiancePass, PrefilterPass, BRDFPass
from editor.render.graphics.passes import LightingPass
from editor.render.graphics.passes import AddPass, TonemappingPass, ClampPass, GaussianblurPass


if __name__ == "__main__":
    import glm
    from editor.render.graphics.viewer import Viewer
    from editor.render.graphics import Scene, Mesh, Geometry, Material
    import time, math

    viewer = Viewer(floating=True)

    # assets
    environment_image = assets.imread('hdri/Tropical_Beach_3k.hdr').astype(np.float32)

    # scene
    scene = Scene.test_scene()
    dirlight = DirectionalLight(direction=glm.vec3(5, -8, -3),
                                color=glm.vec3(1.0) * 1.0,
                                position=glm.vec3(-5, 8, 3),
                                radius=5.0,
                                near=1.0,
                                far=30)

    spotlight = Spotlight(position=glm.vec3(-2, 0.5, -4),
                          direction=glm.vec3(2, -0.5, 4),
                          color=glm.vec3(0.2, 0.18, 0.7) * 1500,
                          fov=45.0,
                          near=1.0,
                          far=30.0)

    pointlight = Pointlight(position=glm.vec3(5, 2, 4),
                            color=glm.vec3(1, 0.7, 0.1) * 500,
                            near=1.0,
                            far=10.0)
    lights = [dirlight, spotlight, pointlight]

    # init passes
    geometry_pass = GeometryPass(viewer.width, viewer.height)
    environment_pass = EnvironmentPass(512, 512)
    irradiance_pass = IrradiancePass(32, 32)
    prefilter_pass = PrefilterPass(128, 128)
    brdf_pass = BRDFPass(512, 512)
    lighting_pass = LightingPass(viewer.width, viewer.height)
    tonemapping_pass = TonemappingPass(viewer.width, viewer.height)
    clamp_pass = ClampPass(viewer.width, viewer.height)
    gaussianblur_pass = GaussianblurPass(viewer.width, viewer.height)
    add_pass = AddPass(viewer.width, viewer.height)

    # texture placeholders
    environment_texture = None
    gBuffer = None
    environment_cubemap = None
    irradiance_cubemap = None
    prefilter_cubemap = None
    brdf_texture = None
    hdr_texture = None
    clamped_texture = None
    blurred_texture = None
    ldr_texture = None
    with_bloom_texture = None


    @viewer.on_setup
    def setup():
        global gBuffer, environment_texture, environment_cubemap, irradiance_cubemap, prefilter_cubemap, brdf_texture, hdr_texture, ldr_texture, clamped_texture
        scene._setup()

        environment_texture = RenderPass.create_texture_from_data(environment_image)
        geometry_pass.setup()
        for light in lights:
            light._setup_shadows()
        environment_pass.setup()
        irradiance_pass.setup()
        prefilter_pass.setup()
        brdf_pass.setup()
        lighting_pass.setup()
        clamp_pass.setup()
        gaussianblur_pass.setup()
        tonemapping_pass.setup()
        add_pass.setup()

        # render passes
        camera360 = Camera360(transform=glm.mat4(1), near=0.1, far=15)

        environment_cubemap = environment_pass.render(environment_texture, camera360)
        irradiance_cubemap = irradiance_pass.render(environment_cubemap, camera360)
        prefilter_cubemap = prefilter_pass.render(environment_cubemap, camera360)
        brdf_texture = brdf_pass.render()


    @viewer.on_draw
    def draw():
        global environment_texture, environment_cubemap
        global irradiance_cubemap, prefilter_cubemap, brdf_texture
        global clamped_texture
        # Render passes
        # -------------
        # geometry
        gBuffer = geometry_pass.render(scene, viewer.camera)

        # shadows
        for light in lights:
            light._render_shadows(scene)

        hdr_texture = lighting_pass.render(viewer.camera.position, lights, gBuffer, irradiance_cubemap,
                                           prefilter_cubemap, brdf_texture)

        ldr_texture = tonemapping_pass.render(hdr_texture, exposure=0.0, gamma=2.2)
        highlights_texture = clamp_pass.render(ldr_texture, minimum=0.95, maximum=1.0)
        blurred_highlights_texture = gaussianblur_pass.render(highlights_texture, iterations=4)
        with_bloom_texture = add_pass.render(ldr_texture, blurred_highlights_texture)

        # Debug
        # -----
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

        # debug beauty
        puregl.imdraw.texture(with_bloom_texture, (0, 0, viewer.width, viewer.height), shuffle=(0, 1, 2, -1))

        # debug postprocessing
        puregl.imdraw.texture(hdr_texture, (0, 300, 90, 90), shuffle=(0, 1, 2, -1))
        puregl.imdraw.texture(highlights_texture, (100, 300, 90, 90), shuffle=(0, 1, 2, -1))
        puregl.imdraw.texture(blurred_highlights_texture, (200, 300, 90, 90), shuffle=(0, 1, 2, -1))
        puregl.imdraw.texture(with_bloom_texture, (300, 300, 90, 90), shuffle=(0, 1, 2, -1))

        # debug shadows
        for i, light in enumerate(lights):
            if isinstance(light, Pointlight):
                puregl.imdraw.cubemap(light._shadow_map, (i * 100, 200, 90, 90), viewer.camera.projection,
                                      viewer.camera.view, shuffle=(0, 0, 0, -1))
            else:
                puregl.imdraw.texture(light._shadow_map, (i * 100, 200, 90, 90), shuffle=(0, 0, 0, -1))

        # debug gBuffer
        gPosition, gNormal, gAlbedo, gEmissive, gRoughness, gMetallic = gBuffer
        puregl.imdraw.texture(gPosition, (0, 0, 90, 90), shuffle=(0, 1, 2, -1))
        puregl.imdraw.texture(gNormal, (100, 0, 90, 90), shuffle=(0, 1, 2, -1))
        puregl.imdraw.texture(gAlbedo, (200, 0, 90, 90), shuffle=(0, 1, 2, -1))
        puregl.imdraw.texture(gEmissive, (300, 0, 90, 90))
        puregl.imdraw.texture(gRoughness, (400, 0, 90, 90), shuffle=(0, 0, 0, -1))
        puregl.imdraw.texture(gMetallic, (500, 0, 90, 90), shuffle=(0, 0, 0, -1))

        # debug IBL
        puregl.imdraw.texture(environment_texture, (0, 100, 90, 90))
        puregl.imdraw.cubemap(environment_cubemap, (100, 100, 90, 90), viewer.camera.projection, viewer.camera.view)
        puregl.imdraw.cubemap(irradiance_cubemap, (200, 100, 90, 90), viewer.camera.projection, viewer.camera.view)
        puregl.imdraw.cubemap(prefilter_cubemap, (300, 100, 90, 90), viewer.camera.projection, viewer.camera.view)
        puregl.imdraw.texture(brdf_texture, (400, 100, 90, 90))


    viewer.start(worker=False)
    print("- end of program -")
