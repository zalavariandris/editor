from OpenGL.GL import *
import numpy as np

class Shader:
    def __enter__(self):
        shaders = {
            GL_VERTEX_SHADER: """
                #version 330 core
                in vec3 position;
                in vec4 color;
                in vec2 uv;

                uniform mat4 modelMatrix;
                uniform mat4 viewMatrix;
                uniform mat4 projectionMatrix;

                uniform sampler2D diffuseMap;

                out vec4 vColor;
                out vec2 vUv;
                void main(){
                  vColor = vec4(color.rgb, 1);
                  vUv = uv;
                  gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1);
                }""",

            GL_FRAGMENT_SHADER: """
                #version 330 core
                out vec4 color;
                in vec4 vColor;
                in vec2 vUv;
                uniform sampler2D diffuseMap;
                void main(){
                  vec4 tex = texture(diffuseMap, vUv);
                  color = vColor*tex;
                }
                """
            }
        self.program_id = glCreateProgram()
        try:
            self.shader_ids = []
            for shader_type, shader_src in shaders.items():
                shader_id = glCreateShader(shader_type)
                glShaderSource(shader_id, shader_src)

                glCompileShader(shader_id)

                # check if compilation was successful
                result = glGetShaderiv(shader_id, GL_COMPILE_STATUS)
                info_log_len = glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH)
                if info_log_len:
                    logmsg = glGetShaderInfoLog(shader_id)
                    print(logmsg)
                    sys.exit(10)

                glAttachShader(self.program_id, shader_id)
                self.shader_ids.append(shader_id)

            glLinkProgram(self.program_id)

            # check if linking was successful
            result = glGetProgramiv(self.program_id, GL_LINK_STATUS)
            info_log_len = glGetProgramiv(self.program_id, GL_INFO_LOG_LENGTH)
            if info_log_len:
                logmsg = glGetProgramInfoLog(self.program_id)
                log.error(logmsg)
                sys.exit(11)

            glUseProgram(self.program_id)
        except Exception as err:
            raise err


        return self

    def __exit__(self, type, value, traceback):
        shader_ids = self.shader_ids
        for shader_id in self.shader_ids:
            glDetachShader(self.program_id, shader_id)
        glUseProgram(0)

    def __del__(self):
        for shader_id in self.shader_ids:
            glDeleteShader(shader_id)
        glDeleteProgram(self.program_id)
        print("delete shader program")

    def get_uniform_location(self, name):
        location = glGetUniformLocation(self.program_id, name)
        assert location>=0
        return location

    def set_uniform(self, name, value):
        location = self.get_uniform_location(name)

        if isinstance(value, np.ndarray):
            if value.shape == (4, 4): # matrix
                glUniformMatrix4fv(location, 1, False, value)
            else:
                raise NotImplementedError
        elif isinstance(value, int):
            glUniform1i(location, value)
        else:
            raise NotImplementedError

    def get_attribute_location(self, attribute_name):
        assert self.program_id == glGetIntegerv(GL_VERTEX_ARRAY_BINDING)
        return glGetAttribLocation(self.program_id, attribute_name)
