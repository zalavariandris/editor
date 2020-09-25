WIDTH, HEIGHT = 1280, 720
from editor.render.graphics.passes import GeometryPass, PBRLightingPass
geometry_pass = GeometryPass(WIDTH, HEIGHT)
lighting_pass = PBRLightingPass(WIDTH, HEIGHT)
from editor.render.graphics import Scene, Mesh, Geometry
from editor.render.graphics.lights import PointLight, SpotLight, DirectionalLight

scene = Scene.test_scene()

from editor.render import puregl
def render():
    gBuffer = geometry_pass.render(scene.find_meshes(), window.camera)
    puregl.imdraw.texture(gBuffer[0], (0,0,WIDTH,HEIGHT))

from editor.render.graphics.window import Window
window = Window(floating=True)

@window.on_draw
def draw():
    render()

window.start(worker=True)