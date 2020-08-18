"""
used references:
- https://metamost.com/opengl-with-python/
"""

from OpenGL import GL as gl
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
        print("{} {:4.0f} fps".format(name, 1.0/deltatime if deltatime>0 else float('inf')))

# help(glfw)

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
        self._callbacks = {"mousemove": [], "mousebutton": []}

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

    def __enter__(self):
        glfw.make_context_current(self._handle)
        gl.glClearColor(*self._clear_color)
        
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


class VBO:
    def __init__(self, data, usage=gl.GL_STATIC_DRAW):
        self._handle = gl.glGenBuffers(1)

        #upload data
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._handle)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.nbytes, data, usage)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def __enter__(self):
        self.glBindBuffer(gl.GL_ARRAY_BUFFER, self._handle)

    def __exit__(self, type, value, traceback):
        self.glBindBuffer(gl.GL_ARRAY_BUFFER, self._handle)

    def __del__(self):
        gl.glDeleteBuffers(1, np.array([self._handle]))


class VAO:
    """
    Vertex Array Object

    Vertex array object stores al of the state needed to supply vertex data.
    It stores the format of the vertex data as well as the Buffer Objects.

    [https://www.khronos.org/opengl/wiki/Vertex_Specification#Vertex_Array_Object]

    """
    def __init__(self):

        # create VAO
        self._handle = gl.glGenVertexArrays(1)
        self._enabled_vertex_attribute_locations = set()

    def set_vertex_attribute(self, location, vbo_handle, size, gtype, normalize=False, stride=0, offset=None):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_handle)
        gl.glVertexAttribPointer(
            location,
            size,
            gtype,
            normalize,
            stride,
            offset
        )
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def enable_vertex_attribute(self, location):
        assert self._handle == gl.glGetIntegerv(gl.GL_VERTEX_ARRAY_BINDING)
        self._enabled_vertex_attribute_locations.add(location)
        gl.glEnableVertexAttribArray(location)

    def disable_vertex_attribute(self, location):
        assert self._handle == gl.glGetIntegerv(gl.GL_VERTEX_ARRAY_BINDING)
        gl.glDisableVertexAttribArray(location)


    def __enter__(self):
        # bind VAO
        gl.glBindVertexArray(self._handle)            
        return self

    def __exit__(self, type, value, traceback):
        for location in self._enabled_vertex_attribute_locations:
            self.disable_vertex_attribute(location)
        # unbind VAO
        assert self._handle == gl.glGetIntegerv(gl.GL_VERTEX_ARRAY_BINDING)
        gl.glBindVertexArray(0)

    def __del__(self):
        # delete VBOs
        # gl.glDeleteBuffers(1, np.array([self.position_vertex_buffer], dtype=np.uint))

        # delete VAO
        gl.glDeleteVertexArrays(1, np.array([self._handle], dtype=np.uint))


class Shader:
    def __enter__(self):
        shaders = {
            gl.GL_VERTEX_SHADER: '''\
                #version 330 core
                in vec3 position;
                in vec4 color;
                uniform mat4 modelMatrix;
                uniform mat4 viewMatrix;
                uniform mat4 projectionMatrix;
                out vec4 vColor;
                void main(){
                  vColor = vec4(color.rgb, 1);
                  gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1);
                }
                ''',
            gl.GL_FRAGMENT_SHADER: '''\
                #version 330 core
                out vec4 color;
                in vec4 vColor;
                void main(){
                  color = vColor;
                }
                '''
            }
        program_id = gl.glCreateProgram()
        try:
            shader_ids = []
            for shader_type, shader_src in shaders.items():
                shader_id = gl.glCreateShader(shader_type)
                gl.glShaderSource(shader_id, shader_src)

                gl.glCompileShader(shader_id)

                # check if compilation was successful
                result = gl.glGetShaderiv(shader_id, gl.GL_COMPILE_STATUS)
                info_log_len = gl.glGetShaderiv(shader_id, gl.GL_INFO_LOG_LENGTH)
                if info_log_len:
                    logmsg = gl.glGetShaderInfoLog(shader_id)
                    print(logmsg)
                    sys.exit(10)

                gl.glAttachShader(program_id, shader_id)
                shader_ids.append(shader_id)

            gl.glLinkProgram(program_id)

            # check if linking was successful
            result = gl.glGetProgramiv(program_id, gl.GL_LINK_STATUS)
            info_log_len = gl.glGetProgramiv(program_id, gl.GL_INFO_LOG_LENGTH)
            if info_log_len:
                logmsg = gl.glGetProgramInfoLog(program_id)
                log.error(logmsg)
                sys.exit(11)

            gl.glUseProgram(program_id)
        except Exception as err:
            raise err
        self.program_id = program_id
        self.shader_ids = shader_ids
        return self

    def __exit__(self, type, value, traceback):
        shader_ids = self.shader_ids
        for shader_id in self.shader_ids:
            gl.glDetachShader(self.program_id, shader_id)
        gl.glUseProgram(0)

    def __del__(self):
        for shader_id in self.shader_ids:
            gl.glDeleteShader(shader_id)
        gl.glDeleteProgram(self.program_id)
        print("delete shader program")


    def get_uniform_location(self, name):
        location = gl.glGetUniformLocation(self.program_id, name)
        assert location>=0
        return location

    def set_uniform(self, name, value):
        location = self.get_uniform_location(name)
        gl.glUniformMatrix4fv(location, 1, False, value)

    def get_attribute_location(self, attribute_name):
        return gl.glGetAttribLocation(self.program_id, attribute_name)




if __name__ == '__main__':
    # variables
    width, height = 640, 480

    # matrices
    model_matrix = np.identity(4)
    view_matrix = glm.lookAt( glm.vec3(2,2,-2), glm.vec3(0,0,0), glm.vec3(0,1,0) )
    projection_matrix = glm.perspective(45, width/height, 1, 100)

    # Create window
    window = Window(width, height, (0, 0, 0.4, 1.0))

    @window.addEventListener("mousemove")
    def mousemove(x, y, dx, dy):
        global view_matrix

        if window.get_mouse_button(0):
            view_matrix = orbit(view_matrix,dx*2,dy*2)

    @window.addEventListener("mousebutton")
    def mousebutton(button, action, modifiers):
        print("mousebutton", button, action, modifiers)

    # Create geometrye
    position_data = np.array(
        [-1, -1, 0,
          1, -1, 0,
          0,  1, 0], 
          dtype=np.float32
    )
    color_data = np.array(
        [ 1, 0, 0,0,
          0, 1, 0,0,
          0,  0, 1,0], 
          dtype=np.float32
    )


    with window: # set gl contex to window
        ctx = glfw.get_current_context()
        print("current context:", ctx)
        position_vbo = VBO(position_data)
        color_vbo = VBO(color_data)
        with Shader() as shader: # use shader program
            vao = VAO()
            with vao: # ise VAO with shader
                for attribute_name, vbo, size in [("position", position_vbo, 3),("color", color_vbo, 4)]:
                    """Enable attributes for current vertex array in shader"""
                    location = shader.get_attribute_location(attribute_name)
                    vao.enable_vertex_attribute(location)
                    vao.set_vertex_attribute(location, vbo._handle, size, gl.GL_FLOAT)

                # start main loop
                while not window.should_close():
                    with profile("draw", disabled=True):
                        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

                        # update uniforms
                        shader.set_uniform("modelMatrix", np.array(model_matrix))
                        shader.set_uniform("viewMatrix", np.array(view_matrix))
                        shader.set_uniform("projectionMatrix", np.array(projection_matrix))

                        # draw
                        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

                        window.swap_buffers()
                        Window.poll_events()

