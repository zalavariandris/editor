if __name__ == "__main__":
	import glm
	from editor.render.graphics.examples.viewer import Viewer
	from editor.render import glsl, puregl, imdraw
	viewer = Viewer()


	scene = Scene()

	@viewer.event
	def on_setup():
		global lambert_program
		lambert_program = puregl.program.create(
		"""#version 330 core
		layout (location=0) in vec3 position;
		layout (location=1) in vec2 uv;
		layout (location=2) in vec3 normal;

		uniform mat4 projection;
		uniform mat4 view;
		uniform mat4 model;

		void main(){
			gl_Position = projection * view * model * vec4(position, 1.0);
		}
		""",
		"""#version 330 core
		uniform vec3 color;
		out vec4 FragColor;
		void main(){
			FragColor = vec4(color, 1.0);
		}
		""")

	@viewer.event
	def on_draw():
		with puregl.program.use(lambert_program):
			puregl.program.set_uniform(lambert_program, "projection", viewer.camera.projection)
			puregl.program.set_uniform(lambert_program, "view", viewer.camera.view)
			puregl.program.set_uniform(lambert_program, "model", glm.mat4(1))
			puregl.program.set_uniform(lambert_program, "color", (1,1,1))
			imdraw.cube(lambert_program)

	viewer.start()