from editor.render.graphics.passes import RenderPass
from editor.render import glsl, puregl
from OpenGL.GL import *


class TemplatePass(RenderPass):
    def __init__(self, width, height, depth_test=False, cull_face=False, blending=False, seamless_cubemap=False):
        super().__init__(width, height, depth_test, cull_face, blending, seamless_cubemap)
        self.program = None
        self.fbo = None
        self.texture = None

    def setup(self):
        super().setup()
        # create program
        # --------------
        self.program.create(
            """#version 330 core
            layout (location=0) in vec3 position;
            layout (location=1) in vec2 uv;
            layout (location=2) in vec3 normal;

            void main(){
                gl_Position = vec4(position);
            }
            """,
            """#version 330 core
            uniform sampler2D input;
            uniform vec2 viewportSize;
            in vec2 TexCoords;
            void main(){
                vec3 color = texture(input, TexCoords);
                FragColor = vec4();
            }
            """
        )

        # create texture(s)
        # ----------------
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)

        # create fbo
        # ----------
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glDrawBuffers(1, [GL_COLOR_ATTACHMENT0+0])
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0+0, GL_TEXTURE_2D, self.texture, 0
        )
        glBindTexture(GL_TEXTURE_2D, 0)

        # create render buffers for depth and stencil
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def render(self, input_texture):
        super().render()
        with puregl.fbo.bind(self.fbo), puregl.program.use(self.program):
            # clear fbo
            glViewport(0, 0, self.width, self.height)
            glClearColor(0.0, 0.0, 0.0, 0.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # configure shader

            # draw
            puregl.imdraw.quad(self.program)
        return self.texture
