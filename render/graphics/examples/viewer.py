from OpenGL.GL import *
import glfw
import glm
import functools
from editor.render import puregl
from editor.render.graphics import PerspectiveCamera

class Viewer:
    def __init__(self, width=1280, height=720, title="puregl-viewer", floating=False):
        self.width, self.height = width, height
        self.title = title
        self._floating = floating

        self.events = {'on_setup':[], 'on_draw':[]}

        # Handle window events
        # -------------
        self.camera = PerspectiveCamera(transform=glm.inverse(glm.lookAt(glm.vec3(1,1.5,4), glm.vec3(0,0,0), glm.vec3(0,1,0))),
                                        fovy=glm.radians(48.5),
                                        aspect=self.width/self.height,
                                        near=0.1,
                                        far=30)

    def event(self, f):
        self.events[f.__name__].append(f)

    def start(self):
        # Create window
        # -------------
        glfw.init()
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.FLOATING, GL_TRUE if self._floating else GL_FALSE)
        window = glfw.create_window(self.width, self.height, self.title, None, None)

        
        # Handle window events
        # --------------------
        glfw.set_input_mode(window, glfw.STICKY_KEYS, True)
        x0 = 0
        y0 = 0
        @functools.partial(glfw.set_mouse_button_callback, window)
        def mousebutton(handle, button, action, modifiers):
            nonlocal x0, y0
            x0, y0 = glfw.get_cursor_pos(window)

        @functools.partial(glfw.set_cursor_pos_callback, window)
        def mousemove(handle, x1, y1):
            nonlocal x0, y0
            if glfw.get_mouse_button(window, 0):
                dx = x1-x0
                dy = y1-y0
                self.camera.transform = glm.inverse(puregl.transform.orbit(glm.inverse(self.camera.transform), dx * 2, dy * 2))
            x0, y0 = x1, y1

        @functools.partial(glfw.set_scroll_callback, window)
        def scroll(handle, dx, dy):
            s = 1 + dy / 10
            self.camera.transform[3].xyz *= glm.vec3(1/s)

        # Start rendering
        # ---------------
        glfw.make_context_current(window)

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

        # fire setup events
        for f in self.events['on_setup']:
            f()

        while not glfw.window_should_close(window):
            glClearColor(0,0,0,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_DEPTH_TEST)

            for f in self.events['on_draw']:
                glViewport(0,0,self.width, self.height)
                f()
            glfw.swap_buffers(window)
            glfw.poll_events()
        glfw.terminate()





