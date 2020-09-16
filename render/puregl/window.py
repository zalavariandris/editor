# opengl
import glfw
from OpenGL.error import GLError

# data
import numpy as np

# threading
from threading import Thread, RLock

# helpers
from editor.render.puregl import imdraw


class Viewer:
    def __init__(self, width=720, height=576, title="Window"):
        self._handle = self.create_window(width, height, title)
        self.setup_events(self._handle)

    @staticmethod
    def create_window(self, width, height, title):
        if not glfw.init():
            return

        try:
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

            window = glfw.create_window(width, height, title, None, None)
            if not window:
                return
        except GLError as err:
            raise err

        return window

    @staticmethod
    def setup_events(window):
        pass

    def onmousemove(self):
        pass

    def onmousebutton(self):
        pass

    def onscroll(self):
        pass

    def onresize(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

    def should_close(self):
        return glfw.window_should_close(self._handle)

    def start(self, worker=False):
        pass

