from OpenGL import GL as gl
import glm
import glfw
import contextlib
import sys
import ctypes
import numpy as np

help(glfw)

# helpers
def orbit(inputMatrix, dx, dy):
    horizontalAxis = glm.vec3( inputMatrix[0][0], inputMatrix[1][0], inputMatrix[2][0] )
    verticalAxis = glm.vec3(0,1,0)

    inputMatrix *= glm.rotate(np.eye(4, dtype=np.float32), dy*0.006, horizontalAxis)
    inputMatrix *= glm.rotate(np.eye(4, dtype=np.float32), dx*0.006, verticalAxis)

    return inputMatrix

import time
@contextlib.contextmanager
def profile(name):
    starttime = time.time()
    yield
    endtime = time.time()
    deltatime = endtime-starttime
    print("{} {:4.0f} fps".format(name, 1.0/deltatime if deltatime>0 else float('inf')))

@contextlib.contextmanager
def create_main_window(width, height):
    if not glfw.init():
        sys.exit(1)
    try:
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        title = 'Tutorial 2: First Triangle'
        window = glfw.create_window(width, height, title, None, None)
        if not window:
            sys.exit(2)
        glfw.make_context_current(window)

        glfw.set_input_mode(window, glfw.STICKY_KEYS, True)
        gl.glClearColor(0, 0, 0.4, 0)
        # glfw.swap_interval( 0 )

        yield window

    finally:
        glfw.terminate()

class VAO:
    def __init__(self, position_data, color_data):
        self.position_data = position_data
        self.color_data = color_data
        # create VAO
        self.vertex_array_id = gl.glGenVertexArrays(1)

        # create VBOs
        self.position_vertex_buffer = gl.glGenBuffers(1)
        self.color_vertex_buffer = gl.glGenBuffers(1)


    def __enter__(self):
        # bind VAO
        gl.glBindVertexArray(self.vertex_array_id)

        # VBOs
        # position
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.position_vertex_buffer)

        array_type = gl.GLfloat * len(position_data)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            len(position_data) * ctypes.sizeof(ctypes.c_float),
            array_type(*position_data),
            gl.GL_STATIC_DRAW
        )

        # upload data
        current_program_id = gl.glGetIntegerv(gl.GL_CURRENT_PROGRAM)
        attr_id = gl.glGetAttribLocation(current_program_id, "position")
        gl.glVertexAttribPointer(
           attr_id,            # attribute .
           3,                  # components per vertex attribute
           gl.GL_FLOAT,        # type
           False,              # to be normalized?
           0,                  # stride
           None                # array buffer offset
        )

        # enable position attribute in VAO
        gl.glEnableVertexAttribArray(attr_id)  # use currently bound VAO
        return self

    def __exit__(self, type, value, traceback):
        # unbind VBOs
        current_program_id = gl.glGetIntegerv(gl.GL_CURRENT_PROGRAM);
        attr_id = gl.glGetAttribLocation(current_program_id, "position")
        gl.glDisableVertexAttribArray(attr_id)

        # unbind VAO
        gl.glBindVertexArray(0)

    def __del__(self):
        # delete VBOs
        gl.glDeleteBuffers(1, np.array([self.position_vertex_buffer], dtype=np.uint))
        # delete VAO
        gl.glDeleteVertexArrays(1, np.array([self.vertex_array_id], dtype=np.uint))


@contextlib.contextmanager
def create_vertex_array_object():
    vertex_array_id = gl.glGenVertexArrays(1)
    try:
        gl.glBindVertexArray(vertex_array_id)
        yield
    finally:
        gl.glDeleteVertexArrays(1, [vertex_array_id])


@contextlib.contextmanager
def create_vertex_buffer(position_data):
    with create_vertex_array_object():
        vertex_buffer = gl.glGenBuffers(1)
        try:
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vertex_buffer)

            array_type = (gl.GLfloat * len(position_data))
            gl.glBufferData(gl.GL_ARRAY_BUFFER,
                            len(position_data) * ctypes.sizeof(ctypes.c_float),
                            array_type(*position_data),
                            gl.GL_STATIC_DRAW)

            current_program_id = gl.glGetIntegerv(gl.GL_CURRENT_PROGRAM);
            attr_id = gl.glGetAttribLocation(current_program_id, "position")
            gl.glVertexAttribPointer(
               attr_id,            # attribute .
               3,                  # components per vertex attribute
               gl.GL_FLOAT,        # type
               False,              # to be normalized?
               0,                  # stride
               None                # array buffer offset
            )
            gl.glEnableVertexAttribArray(attr_id)  # use currently bound VAO
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            yield
        finally:
            gl.glDisableVertexAttribArray(attr_id)
            gl.glDeleteBuffers(1, [vertex_buffer])


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
                  vColor = vec4(0,1,0,1);
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

# variables
width, height = 640, 480
# A triangle
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
model_matrix = np.identity(4)
view_matrix = glm.lookAt( glm.vec3(2,2,-2), glm.vec3(0,0,0), glm.vec3(0,1,0) )
projection_matrix = glm.perspective(45, width/height, 1, 100)
prev_mouse_pos = None


if __name__ == '__main__':
    def on_mousemove(window, x, y):
        global view_matrix, projection_matrix, model_matrix
        global prev_mouse_pos
        if prev_mouse_pos is not None:
            dx, dy = x-prev_mouse_pos[0], y-prev_mouse_pos[1]
        else:
            dx, dy = 0,0

        if glfw.get_mouse_button(window, 0):
            view_matrix = orbit(view_matrix,dx*2,dy*2)
        prev_mouse_pos = glfw.get_cursor_pos(window)

    def on_mousebutton(window, button, action, modifiers):
        LEFT_BUTTON = 0
        RIGHT_BUTTON = 1
        MIDDLE_BUTTON = 2

        IS_PRESS = action is 1
        IS_RELEASE = action is 0

        NO_MODIFIER = 0
        SHIFT_MODIFIER = 1
        CTRL_MODIFIER = 2
        ALT_MODIFIER = 4

        # print(button, action, modifiers)
        prev_mouse_pos = glfw.get_cursor_pos(window)

    with create_main_window(width, height) as window:
        glfw.set_cursor_pos_callback(window, on_mousemove);
        glfw.set_mouse_button_callback(window, on_mousebutton)
        with Shader() as shader:
            with VAO(position_data, color_data):
                # start main loop
                while glfw.get_key(window, glfw.KEY_ESCAPE) != glfw.PRESS and not glfw.window_should_close(window):
                    with profile("draw"):
                        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

                        # update uniforms
                        shader.set_uniform("modelMatrix", np.array(model_matrix))
                        shader.set_uniform("viewMatrix", np.array(view_matrix))
                        shader.set_uniform("projectionMatrix", np.array(projection_matrix))

                        # draw
                        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)
                        glfw.swap_buffers(window)
                        glfw.poll_events()

