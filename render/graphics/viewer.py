from editor.render.graphics.passes.deferred_pbr_renderer import DeferredPBRRenderer
from editor.render import puregl, imdraw
from OpenGL.GL import *
import glm
import glfw
import functools
from threading import Thread
import logging
from editor.render.graphics import PerspectiveCamera
logging.basicConfig(filename=None, level=logging.DEBUG, format='%(levelname)s:%(module)s.%(funcName)s: %(message)s')


class Viewer:
    def __init__(self, scene, width=1280, height=720, title="Viewer", floating=False, background_color=(0,0,0,1)):
        # window
        self.width = width
        self.height = height
        self.scene = scene
        self.title = title
        self._floating = floating
        self.background_color = background_color

        # threading
        self.thread = None
        self.lock = None

        # renderer
        from editor.render.graphics import PerspectiveCamera
        self.camera = PerspectiveCamera(glm.mat4(1), glm.radians(39.6), self.width/self.height, 0.1, 30)
        self.camera.transform = glm.inverse(glm.lookAt(glm.vec3(2, 3, 6), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0)))
        self.renderer = DeferredPBRRenderer(self.width, self.height)

    def create_window(self):
        # Create window
        # -------------
        if not glfw.init():
            raise Exception("can`t init glfw")

        # Create a windowed mode window and its OpenGL context
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.FLOATING, GL_TRUE if self._floating else GL_FALSE)
        self._handle = glfw.create_window(self.width, self.height, self.title, None, None)
        if not self._handle:
            glfw.terminate()
            raise Exception("cant create glfw window")

        # Handle events
        # -------------
        # COMMENT: this migth be uesful later, when implementing keyboard events
        glfw.set_input_mode(self._handle, glfw.STICKY_KEYS, True)
        x0 = 0
        y0 = 0
        @functools.partial(glfw.set_mouse_button_callback, self._handle)
        def mousebutton(handle, button, action, modifiers):
            nonlocal x0, y0
            x0, y0 = glfw.get_cursor_pos(self._handle)

        @functools.partial(glfw.set_cursor_pos_callback, self._handle)
        def mousemove(handle, x1, y1):
            nonlocal x0, y0
            if glfw.get_mouse_button(self._handle, 0):
                dx = x1-x0
                dy = y1-y0
                self.camera.transform = glm.inverse(puregl.transform.orbit(glm.inverse(self.camera.transform), dx * 2, dy * 2))
            x0, y0 = x1, y1

        @functools.partial(glfw.set_scroll_callback, self._handle)
        def scroll(handle, dx, dy):
            s = 1 + dy / 10
            self.camera.position *= glm.vec3(1/s)

    def start(self, worker=False):
        if worker:
            self.thread = Thread(target=self._start)
            self.thread.start()
        else:
            self._start()

    def _start(self, worker=False):
        self.create_window()
        glfw.make_context_current(self._handle)

        # print info
        import sys
        print("+------------------ Python Info ------------------")
        print("| executable           ", sys.executable)
        print("| version              ", ".".join(str(v) for v in sys.version_info))
        print("|")
        print("+------------------ OpenGL Info ------------------")
        print("| VENDOR               ", glGetString(GL_VENDOR).decode('UTF-8'))
        print("| RENDERER             ", glGetString(GL_RENDERER).decode('UTF-8'))
        print("| MAX_DRAW_BUFFERS     ", glGetIntegerv(GL_MAX_DRAW_BUFFERS))
        print("| MAX_COLOR_ATTACHMENTS", glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS))
        print("|")
        print("+-------------------------------------------------")

        
        # main loop
        while not glfw.window_should_close(self._handle):
            glClearColor(*self.background_color)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_DEPTH_TEST)

            if self.lock:
                with self.lock:
                    self.draw()
            else:
                self.draw()

                glfw.swap_buffers(self._handle)
                glfw.poll_events()
        glfw.terminate()

    def draw(self):

        # Draw
        # ----
        beauty = self.renderer.render(self.scene, self.camera)
        imdraw.texture(beauty, (0,0,self.width, self.height))
        imdraw.axis(self.camera.projection, self.camera.view)



if __name__ == "__main__":
    # from editor.render.graphics.examples.viewer import Viewer as TestViewer

    # viewer = TestViewer()


    # @viewer.event
    # def on_draw():
    #     pass
    # viewer.start()


    from editor.render.graphics import Scene, Mesh, Geometry, Material, PointLight, SpotLight, DirectionalLight
    import numpy as np
    scene = Scene()
    for j in range(2):
        for x, roughness in zip(np.linspace(-6,6, 10), np.linspace(0,1, 10)):
            scene.add_child(Mesh(transform=glm.translate(glm.mat4(1), (x,0.5, j*1.5)),
                          geometry=Geometry(*imdraw.geo.sphere()),
                          material=Material(albedo=glm.vec3(0.5),
                                            emission=(0,0,0),
                                            roughness=roughness,
                                            metallic=float(j))))

    for j in range(2):
        for x, roughness in zip(np.linspace(-6,6, 10), np.linspace(0,1, 10)):
            scene.add_child(Mesh(transform=glm.translate(glm.mat4(1), (x,0.5, j*1.5-3)),
                          geometry=Geometry(*imdraw.geo.sphere()),
                          material=Material(albedo=glm.vec3(0.5),
                                            emission=(0,0,0),
                                            roughness=glm.pow(roughness, 2),
                                            metallic=float(j))))

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

    viewer = Viewer(scene, floating=True)
    viewer.start(worker=False)
    print("-- end of program --")


