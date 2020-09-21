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
        from pathlib import Path
        path = Path("../../assets/test_scene.glb").resolve()
        triscene = trimesh.load(path)

        print( [name for name in triscene.geometry.keys()] )
        sphere = triscene.geometry['Sphere']


        derived_geo=Geometry(positions=sphere.vertices.astype(np.float32),
                             normals=sphere.vertex_normals.astype(np.float32),
                             uvs=sphere.visual.uv.astype(np.float32),
                             indices=sphere.faces.astype(np.uint))

        sphere = Mesh(transform=glm.mat4(1),
                      geometry=derived_geo,#Geometry(*puregl.geo.sphere()),
                      material=Material(albedo=glm.vec3(0.5),
                                        emission=(0,0,0),
                                        roughness=0.5,
                                        metallic=0.0))
    
        scene = Scene.test_scene()
        scene.add_child(sphere)


        window = Window(floating=True)
        renderer = DeferredPBRRenderer(window.width, window.height)


        @window.on_draw
        def draw():
            beauty = renderer.render(scene, window.camera)
            puregl.imdraw.texture(beauty, (0, 0, window.width, window.height))


        window.start(worker=False)
        print("- end of program -")