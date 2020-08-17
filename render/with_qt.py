from OpenGL import GL as gl
import glm
import glfw
import contextlib
import sys
import ctypes
import numpy as np

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

        yield window

    finally:
        glfw.terminate()

@contextlib.contextmanager
def create_vertex_array_object():
    vertex_array_id = gl.glGenVertexArrays(1)
    try:
        gl.glBindVertexArray(vertex_array_id)
        yield
    finally:
        gl.glDeleteVertexArrays(1, [vertex_array_id])

@contextlib.contextmanager
def create_vertex_buffer(program_id, vertex_data):
    with create_vertex_array_object():
        attr_id = gl.glGetAttribLocation(program_id, "position")

        vertex_buffer = gl.glGenBuffers(1)
        try:
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vertex_buffer)

            array_type = (gl.GLfloat * len(vertex_data))
            gl.glBufferData(gl.GL_ARRAY_BUFFER,
                            len(vertex_data) * ctypes.sizeof(ctypes.c_float),
                            array_type(*vertex_data),
                            gl.GL_STATIC_DRAW)

            gl.glVertexAttribPointer(
               attr_id,            # attribute 0.
               3,                  # components per vertex attribute
               gl.GL_FLOAT,        # type
               False,              # to be normalized?
               0,                  # stride
               None                # array buffer offset
            )
            gl.glEnableVertexAttribArray(attr_id)  # use currently bound VAO
            yield
        finally:
            gl.glDisableVertexAttribArray(attr_id)
            gl.glDeleteBuffers(1, [vertex_buffer])


@contextlib.contextmanager
def create_shader():
    shaders = {
        gl.GL_VERTEX_SHADER: '''\
            #version 330 core
            in vec3 position;
            uniform mat4 modelMatrix;
            uniform mat4 viewMatrix;
            uniform mat4 projectionMatrix;
            void main(){
              gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1);
            }
            ''',
        gl.GL_FRAGMENT_SHADER: '''\
            #version 330 core
            out vec3 color;
            void main(){
              color = vec3(0,1,1);
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
        yield program_id
    finally:
        for shader_id in shader_ids:
            gl.glDetachShader(program_id, shader_id)
            gl.glDeleteShader(shader_id)
        gl.glUseProgram(0)
        gl.glDeleteProgram(program_id)

def create_viewMatrix(program_id):
    viewMatrix = glm.lookAt( glm.vec3(2,2,-2), glm.vec3(0,0,0), glm.vec3(0,1,0) )
    location = gl.glGetUniformLocation(program_id, 'viewMatrix')
    assert location>=0
    return location, viewMatrix

def create_modelMatrix(program_id):
    modelMatrix = np.identity(4)
    location = gl.glGetUniformLocation(program_id, 'modelMatrix')
    assert location>=0
    return location, modelMatrix

def create_projectionMatrix(program_id, width, height):
    projectionMatrix = glm.perspective(45, width/height, 1, 100) 

    matrix_id = gl.glGetUniformLocation(program_id, 'projectionMatrix')
    assert matrix_id>=0
    return matrix_id, projectionMatrix

def main_loop(window, model_location, model_matrix, view_location, view_matrix, projection_location, projection_matrix):
    while (
        glfw.get_key(window, glfw.KEY_ESCAPE) != glfw.PRESS and
        not glfw.window_should_close(window)
    ):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        # set uniforms
        gl.glUniformMatrix4fv(model_location, 1, False, np.array(model_matrix))
        gl.glUniformMatrix4fv(view_location, 1, False, np.array(view_matrix))
        gl.glUniformMatrix4fv(projection_location, 1, False, np.array(projection_matrix))
        # draw
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)
        glfw.swap_buffers(window)
        glfw.poll_events()

if __name__ == '__main__':
    width, height = 640, 480
    # A triangle
    vertex_data = np.array([-1, -1, 0,
                    1, -1, 0,
                    0,  1, 0], dtype=np.float32)

    with create_main_window(width, height) as window:
        with create_shader() as program_id:
            with create_vertex_buffer(program_id, vertex_data):
                model_location, model_matrix = create_modelMatrix(program_id)
                view_location, view_matrix = create_viewMatrix(program_id)
                projection_location, projection_matrix = create_projectionMatrix(program_id, width, height)
                main_loop(window, model_location, model_matrix, view_location, view_matrix, projection_location, projection_matrix)

