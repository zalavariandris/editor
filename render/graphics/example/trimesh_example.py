if __name__ == "__main__":
    import logging
    from editor.render.graphics.window import Window
    from editor.render.graphics.passes.deferred_pbr_renderer import DeferredPBRRenderer
    from editor.render.graphics.passes.deferred_matcap_renderer import DeferredMatcapRenderer
    from editor.render.graphics import Mesh, Geometry, Scene, Material
    from editor.render import puregl
    import trimesh
    # logging.basicConfig(level=logging.DEBUG)

    if __name__ == "__main__":
        import numpy as np
        import glm
        from editor.render.graphics import Scene
        from editor.render.graphics.lights import PointLight, DirectionalLight
        from pathlib import Path
        path = Path("../../assets/test_scene.glb").resolve()
        triscene = trimesh.load(str(path))
        scene = Scene.from_trimesh_scene(triscene)
        scene.plot()

        dirlight = DirectionalLight(direction=glm.vec3(5, -8, -3),
                                    color=glm.vec3(1.0),
                                    position=glm.vec3(-5, 8, 3),
                                    radius=5.0,
                                    near=1.0,
                                    far=30)
        scene.add_child(dirlight)

        pointlight = PointLight(position=glm.vec3(5, 2, 4),
                                color=glm.vec3(1, 0.7, 0.1) * 500,
                                near=1.0,
                                far=10.0)
        scene.add_child(pointlight)

        window = Window(floating=True)
        renderer = DeferredPBRRenderer(window.width, window.height)

        @window.on_draw
        def draw():
            beauty = renderer.render(scene, window.camera)
            puregl.imdraw.texture(beauty, (0, 0, window.width, window.height))


        window.start(worker=False)
        print("- end of program -")