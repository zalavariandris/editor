"""
used references:
- https://metamost.com/opengl-with-python/
"""

from OpenGL.GL import *
from OpenGL.error import GLError, NullFunctionError
import glm
import glfw
import contextlib
import sys
import ctypes
import numpy as np
from editor.render.gloo.helpers import orbit, plane, box, sphere
from editor.utils import profile

import functools
from pathlib import Path

class GLFWWindow:
    def __init__(self, width, height, clear_color=(0,0,0,1)):
        # attributes
        self._clear_color = clear_color
        
        # gl context and window
        if not glfw.init():
            sys.exit(1)

        try:
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

            title = "Window"

            # create window
            self._handle = glfw.create_window(width, height, title, None, None)
            if not self._handle:
                sys.exit(2)

        except GLError as err:
            raise err

        # Events
        glfw.set_input_mode(self._handle, glfw.STICKY_KEYS, True) #FIXE: this migth be ueful later, when implementing keyboard events
        self._callbacks = {"mousemove": [], "mousebutton": [], 'scroll':[], 'resize':[]}

        # mouse
        prev_mouse_pos = (0,0)
        @functools.partial(glfw.set_cursor_pos_callback, self._handle)
        def mousemove(handle, x, y):
            nonlocal prev_mouse_pos
            for callback in self._callbacks["mousemove"]:
                callback(x,y,x-prev_mouse_pos[0],y-prev_mouse_pos[1])
            prev_mouse_pos = x,y

        @functools.partial(glfw.set_mouse_button_callback, self._handle)
        def mousebutton(handle, button, action, modifiers):
            nonlocal prev_mouse_pos
            for callback in self._callbacks["mousebutton"]:
                callback(button, action, modifiers)
            prev_mouse_pos = glfw.get_cursor_pos(self._handle)

        @functools.partial(glfw.set_scroll_callback, self._handle)
        def scroll(handle, dx, dy):
            for callback in self._callbacks['scroll']:
                callback(dx, dy)

        @functools.partial(glfw.set_window_size_callback, self._handle)
        def resize(handle, width, height):
            for callback in self._callbacks['resize']:
                self._width, self._height = width, height
                callback(width, height)

        self._width, self._height = width, height


    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def __enter__(self):
        glfw.make_context_current(self._handle)
        glClearColor(*self._clear_color)
        
        return self

    def __exit__(self, type, value, traceback):
        pass
        # glfw.destroy_window(self._handle)

    def destroy(self):
        glfw.destroy_window(self._handle)

    def __del__(self):
         #FIXME: delete occurs after window handle is not valid
        glfw.terminate()

    def should_close(self):
        return glfw.window_should_close(self._handle)

    def get_mouse_button(self, button):
        return glfw.get_mouse_button(self._handle, button)

    """ attach event handlers """
    def addEventListener(self, event, function=None):
        """
        Attach an event handlers to events.

        can also be used as a decorator
        like so:
        @addEventListener("mousemove")
        def myMousemoveCallback(x, y)
        """

        if function is not None:
            # used directly
            self._callbacks[event].append(function)
        else:
            # used as a decorator
            return functools.partial(self.addEventListener, event)

    def swap_buffers(self):
        glfw.swap_buffers(self._handle)

    @staticmethod
    def poll_events():
        glfw.poll_events()

import math
import time
from editor.render.gloo.helpers import orbit
class GLFWViewer(GLFWWindow):
    def __init__(self, width, height, clear_color=(0.3,0.1,0.1,1)):
        super().__init__(width, height, clear_color)

        self.view_matrix = glm.lookAt( glm.vec3(0, 1,4), glm.vec3(0,0.0,0), glm.vec3(0,1,0) )
        self.projection_matrix = glm.perspective(math.radians(60), width/height, 0.1, 100)

        @self.addEventListener("mousemove")
        def mousemove(x, y, dx, dy):
            if self.get_mouse_button(0):
                self.view_matrix = orbit(self.view_matrix, dx*2,dy*2)

        @self.addEventListener("mousebutton")
        def mousebutton(button, action, modifiers):
            pass

        @self.addEventListener("scroll")
        def scroll(dx, dy):
            s = 1+dy/10
            self.view_matrix = glm.scale(self.view_matrix, (s,s,s))

        @self.addEventListener("resize")
        def resize(w, h):
            glViewport(0, 0, w, h)
            self.projection_matrix = glm.perspective(math.radians(60), w/h, 1, 100)

        self._callbacks['setup'] = []
        self._callbacks['draw'] = []

    def start(self):
        with self:
            for setup in self._callbacks['draw']:
                setup()

        while not self.should_close():
            with self:
                for draw in self._callbacks['draw']:
                    draw()

            # time.sleep(1/60)
            GLFWViewer.poll_events()