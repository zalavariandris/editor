from OpenGL.GL import *
import glfw

class Viewer:
    def __init__(self):
        self.events = {'on_setup':[], 'on_draw':[]}

    def event(self, f):
        self.events[f.__name__].append(f)

    def start(self):
        glfw.init()
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        window = glfw.create_window(1280, 720, "Lines example", None, None)
        glfw.make_context_current(window)
        # fire setup events
        for f in self.events['on_setup']:
            f()

        while not glfw.window_should_close(window):
            glClearColor(0,0,0,1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_DEPTH_TEST)

            for f in self.events['on_draw']:
                f()
            glfw.swap_buffers(window)
            glfw.poll_events()
        glfw.terminate()





