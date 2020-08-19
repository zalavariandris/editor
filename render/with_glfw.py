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

import time
@contextlib.contextmanager
def profile(name, disabled=False):
    starttime = time.time()
    yield
    endtime = time.time()
    deltatime = endtime-starttime
    if not disabled:
        print("{} {:4.0} fps".format(name, 1.0/deltatime if deltatime>0 else float('inf')))

# helpers
def orbit(inputMatrix, dx, dy):
    horizontalAxis = glm.vec3( inputMatrix[0][0], inputMatrix[1][0], inputMatrix[2][0] )
    verticalAxis = glm.vec3(0,1,0)

    inputMatrix *= glm.rotate(np.eye(4, dtype=np.float32), dy*0.006, horizontalAxis)
    inputMatrix *= glm.rotate(np.eye(4, dtype=np.float32), dx*0.006, verticalAxis)

    return inputMatrix

import functools
class Window:
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
        self._callbacks = {"mousemove": [], "mousebutton": [], 'scroll':[]}

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

    def __enter__(self):
        glfw.make_context_current(self._handle)
        glClearColor(*self._clear_color)
        
        return self

    def __exit__(self, type, value, traceback):
        pass

    def __del__(self):
        glfw.destroy_window(self._handle)
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
        example:
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

from vbo import VertexBuffer, IndexBuffer
from vao import VAO
from fbo import FBO
from shader import Shader
from texture import Texture

def box(width=1, height=1, length=1, origin=(0,0)):
    """ create flat cube
    [https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Tutorial/Creating_3D_objects_using_WebGL]
    """
    # Create geometry
    positions = np.array([
        # Front face
        -1.0, -1.0,  1.0,
        1.0, -1.0,  1.0,
        1.0,  1.0,  1.0,
        -1.0,  1.0,  1.0,

        # Back face
        -1.0, -1.0, -1.0,
        -1.0,  1.0, -1.0,
        1.0,  1.0, -1.0,
        1.0, -1.0, -1.0,

        # Top face
        -1.0,  1.0, -1.0,
        -1.0,  1.0,  1.0,
        1.0,  1.0,  1.0,
        1.0,  1.0, -1.0,

        # Bottom face
        -1.0, -1.0, -1.0,
        1.0, -1.0, -1.0,
        1.0, -1.0,  1.0,
        -1.0, -1.0,  1.0,

        # Right face
        1.0, -1.0, -1.0,
        1.0,  1.0, -1.0,
        1.0,  1.0,  1.0,
        1.0, -1.0,  1.0,

        # Left face
        -1.0, -1.0, -1.0,
        -1.0, -1.0,  1.0,
        -1.0,  1.0,  1.0,
        -1.0,  1.0, -1.0,
    ], dtype=np.float32).reshape((-1,3))

    positions/=2, 2, 2
    positions*=width, height, length
    positions[:,0:2]-=origin


    indices = np.array([
        0,  1,  2,      0,  2,  3,    # front
        4,  5,  6,      4,  6,  7,    # back
        8,  9,  10,     8,  10, 11,   # top
        12, 13, 14,     12, 14, 15,   # bottom
        16, 17, 18,     16, 18, 19,   # right
        20, 21, 22,     20, 22, 23,   # left
    ], dtype=np.uint).reshape((-1,3))

    uvs = np.array([
       # Front
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Back
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Top
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Bottom
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Right
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
        # Left
        0.0,  0.0,
        1.0,  0.0,
        1.0,  1.0,
        0.0,  1.0,
    ], dtype=np.float32)

    colors = np.repeat(np.array([
        [1.0,  1.0,  1.0,  1.0],    # Front face: white
        [1.0,  0.0,  0.0,  1.0],    # Back face: red
        [0.0,  1.0,  0.0,  1.0],    # Top face: green
        [0.0,  0.0,  1.0,  1.0],    # Bottom face: blue
        [1.0,  1.0,  0.0,  1.0],    # Right face: yellow
        [1.0,  0.0,  1.0,  1.0],    # Left face: purple
    ]), 4, axis=0).astype(np.float32)
    # FIXME: Repeat each color four times for the four vertices of the face

    return {
        'positions': positions,
        'indices':   indices,
        'uvs':       uvs,
        'colors':    colors
        }

def plane(width=1, length=1, origin=(0,0)):
    # Create geometry
    positions = np.array([
        -1, 0, -1,
         1, 0, -1,
         1, 0,  1,
        -1, 0,  1
    ], dtype=np.float32).reshape((-1,3))
    positions/=2, 2, 2
    positions*=width, height, length
    positions[:,0:2]-=origin

    indices = np.array([
        0,1,2,
        0,2,3
    ], dtype=np.uint).reshape((-1,3))

    uvs = np.array([
         0,  0,
         1,  0,
         1,  1,
         0,  1
    ],dtype=np.float32).reshape((-1,2))

    colors = np.array([
         1, 1, 1, 1,
         1, 1, 1, 1,
         1, 1, 1, 1,
         1, 1, 1, 1
    ],dtype=np.float32).reshape((-1,4))

    return {
        'positions': positions,
        'indices':   indices,
        'uvs':       uvs,
        'colors':    colors
        }


if __name__ == '__main__':
    import math
    # variables
    width, height = 640, 480

    # matrices
    model_matrix = np.identity(4)
    view_matrix = glm.lookAt( glm.vec3(0, 1,-4), glm.vec3(0,0,0), glm.vec3(0,1,0) )
    projection_matrix = glm.perspective(math.radians(60), width/height, 1, 100)

    # Create window
    window = Window(width, height, (0, 0, 0.4, 1.0))

    @window.addEventListener("mousemove")
    def mousemove(x, y, dx, dy):
        global view_matrix
        if window.get_mouse_button(0):
            view_matrix = orbit(view_matrix, dx*2,dy*2)

    @window.addEventListener("mousebutton")
    def mousebutton(button, action, modifiers):
        pass

    @window.addEventListener("scroll")
    def scroll(dx, dy):
        global view_matrix
        s = 1+dy/10
        view_matrix = glm.scale(view_matrix, (s,s,s))

    # create geometry
    plane_geometry = plane(width=3, length=3)
    box_geometry = box(origin=(0,-0.5))
    cctv_geometry = plane(1,1)

    # transform vertices to model position
    model = glm.mat4(1)
    model = glm.translate(model, glm.vec3(0.2, 1.8, 0))
    model = glm.rotate(model, math.radians(90), glm.vec3(0, 0, 1))
    model = glm.scale(model, glm.vec3(0.5, 0.5, 1))
    cctv_modelmatrix = model

    with window: # set gl contex to window
        ctx = glfw.get_current_context()

        glEnable(GL_DEPTH_TEST)

        box_bufferattributes = {
            'position': (VertexBuffer(box_geometry['positions']), 3),
            'color':    (VertexBuffer(box_geometry['colors']),    4),
            'uv':       (VertexBuffer(box_geometry['uvs']),       2),
            'indices':  (IndexBuffer(box_geometry['indices']),    1)
        }

        plane_bufferattributes = {
            'position': (VertexBuffer(plane_geometry['positions']), 3),
            'color':    (VertexBuffer(plane_geometry['colors']),    4),
            'uv':       (VertexBuffer(plane_geometry['uvs']),       2),
            'indices':  (IndexBuffer(plane_geometry['indices']),    1)
        }

        cctv_bufferattributes = {
            'position': (VertexBuffer(cctv_geometry['positions']), 3),
            'color':    (VertexBuffer(cctv_geometry['colors']),    4),
            'uv':       (VertexBuffer(cctv_geometry['uvs']),       2),
            'indices':  (IndexBuffer(cctv_geometry['indices']),    1)
        }

        # Create gradient texture
        gradient_data = np.ones( (64,64,3) ).astype(np.float32)
        xv, yv = np.meshgrid(np.linspace(0,1,64),np.linspace(0,1,64))
        gradient_data[:,:,0] = 1
        gradient_data[:,:,1] = xv.astype(np.float32)
        gradient_data[:,:,2] = yv.astype(np.float32)
        gradient_texture = Texture(gradient_data, 0)

        # Create noise texture
        noise_data = np.random.uniform( 0,1, (64*64*3)).astype(np.float32)
        noise_texture = Texture(noise_data, 0)

        vao = VAO()
        with Shader() as shader: # use shader program
            # start main loop
            while not window.should_close():
                with profile("draw", disabled=True):
                    # clear background
                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                    # update uniforms
                    shader.set_uniform("modelMatrix", np.array(model_matrix))
                    shader.set_uniform("viewMatrix", np.array(view_matrix))
                    shader.set_uniform("projectionMatrix", np.array(projection_matrix))
                    shader.set_uniform("diffuseMap", gradient_texture.texture_unit)

                    # update attributes
                    with vao:
                        # set vao to geometry vbos
                        for attributes, texture in [(box_bufferattributes, noise_texture), (plane_bufferattributes, gradient_texture), (cctv_bufferattributes, None)]:
                            for name, attribute in attributes.items():
                                if name!='indices':
                                    vbo, size = attribute
                                    """Enable attributes for current vertex array in shader"""
                                    location = shader.get_attribute_location(name)
                                    vao.enable_vertex_attribute(location)

                                    # set attribute pointer in shader
                                    vao.set_vertex_attribute(location, vbo._handle, size, GL_FLOAT)
                            
                            # draw object
                            indexBuffer = attributes['indices'][0]
                            with indexBuffer:
                                count = indexBuffer.count
                                if texture:
                                    with texture(0):
                                        glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
                                else:
                                    glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)

                        window.swap_buffers()
                        Window.poll_events()

