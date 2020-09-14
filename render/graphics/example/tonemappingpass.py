from renderpass import RenderPass
from OpenGL.GL import *
from editor.render.puregl import imdraw, program, texture, fbo

class TonemappingPass(RenderPass):
	def __init__(self, width, height):
		super().__init__(width, height, False, GL_BACK)
		self.hdrimage = None
		self.exposure = 0.0
		self.gamma = 2.2

	def setup(self):
		# create program
		self.prog = program.create(
			"""#version 330 core
			out vec2 TexCoords;

			layout (location = 0) in vec3 position;
			layout (location = 1) in vec2 uv;
			layout (location = 2) in vec3 normal;

			void main(){
			    TexCoords = uv;
			    gl_Position = vec4(position.xy, 0.0, 1.0);
			}
			""",
			"""#version 330 core
			out vec4 FragColor;
			in vec2 TexCoords;
			uniform sampler2D screenTexture;
			uniform sampler2D bloomBlur;
			uniform float exposure;
			uniform float gamma=2.2;

			void main(){
			    vec3 hdrColor = texture(screenTexture, TexCoords).rgb;
			    vec3 bloomColor = texture(bloomBlur, TexCoords).rgb;
			    vec3 color=hdrColor+bloomColor;
			    
			    // reinhardt tonemapping
			    // vec3 mapped = hdrColor / (hdrColor+vec3(1.0));

			    // exposure tone mapping
			    color = vec3(1.0) - exp(-hdrColor * pow(2, exposure)); // FIXME: use f-stop, shutterspeed, aperturesize

			    // gamma correction
			    color = pow(color, vec3(1.0 / gamma));  

			    FragColor = vec4(color, 1.0);
			}
			""")

		# create texture
		self.ldrimage = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, self.ldrimage)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, self.width, self.height, 0, GL_RGBA, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glBindTexture(GL_TEXTURE_2D, 0)

		# create depth+stencil buffer
		rbo = glGenRenderbuffers(1)
		glBindRenderbuffer(GL_RENDERBUFFER, rbo)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
		glBindRenderbuffer(GL_RENDERBUFFER, 0)

		# create fbo
		self.fbo = glGenFramebuffers(1)
		with fbo.bind(self.fbo):
			glFramebufferTexture2D(
				GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.ldrimage, 0
			)
			# attach depth and stencil component
			glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)
			
			assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE

	def render(self):
		assert self.hdrimage is not None
		glCullFace(GL_BACK)
		glDisable(GL_DEPTH_TEST)
		with fbo.bind(self.fbo), program.use(self.prog) as prog:
			glViewport(0,0,self.width, self.height)
			glClearColor(0,0,0,0)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

			glActiveTexture(GL_TEXTURE0+0)
			glBindTexture(GL_TEXTURE_2D, self.hdrimage)

			program.set_uniform(prog, 'screenTexture', 0)
			program.set_uniform(prog, 'bloomBlur', 1)
			program.set_uniform(prog, 'exposure', self.exposure)
			program.set_uniform(prog, 'gamma', self.gamma)

			imdraw.quad(prog)
