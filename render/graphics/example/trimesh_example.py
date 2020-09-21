if __name__ == "__main__":
    import logging
    from editor.render.graphics.window import Window
    from editor.render.graphics.passes.deferred_pbr_renderer import DeferredPBRRenderer
    from editor.render import puregl
    import trimesh
    logging.basicConfig(level=logging.DEBUG)

    if __name__ == "__main__":
        import glm
        from pathlib import Path
        path = Path("../../assets/test_scene.glb").resolve()
        tri = trimesh.load(path)
        print(tri)

        from editor.render.graphics import Scene

        scene = Scene.test_scene()

        viewer = Window(floating=True)
        renderer = DeferredPBRRenderer(viewer.width, viewer.height)


        @viewer.on_draw
        def setup():
            beauty = renderer.render(scene, viewer.camera)
            puregl.imdraw.texture(beauty, (0, 0, viewer.width, viewer.height))


        viewer.start(worker=False)
        print("- end of program -")