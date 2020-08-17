

import numpy as np
from glumpy import app, gl, gloo
# from glumpy import glm
import glm
from typing import Tuple

# Helpers
def lookAt(center, target, up):
    f = (target - center); f = f/np.linalg.norm(f)
    s = np.cross(f, up); s = s/np.linalg.norm(s)
    u = np.cross(s, f); u = u/np.linalg.norm(u)

    m = np.zeros((4, 4))
    m[0, :-1] = s
    m[1, :-1] = u
    m[2, :-1] = -f
    m[-1, -1] = 1.0

    return m

# Initalize
vertexShader = None
fragmentShader = None
geometry = None

def createShader():
	global vertexShader, fragmentShader
	vertexShader = """
		// Built-in uniforms and attributes

		// = object.matrixWorld
		uniform mat4 modelMatrix;

		// = camera.matrixWorldInverse * object.matrixWorld
		uniform mat4 modelViewMatrix;

		// = camera.projectionMatrix
		uniform mat4 projectionMatrix;

		// = camera.matrixWorldInverse
		uniform mat4 viewMatrix;

		// = inverse transpose of modelViewMatrix
		uniform mat3 normalMatrix;

		// = camera position in world space
		uniform vec3 cameraPosition;

		// default vertex attributes provided by Geometry and BufferGeometry
		attribute vec3 position;
		attribute vec3 normal;
		attribute vec2 uv;

		void main()
		{
			gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
		} """

	fragmentShader = """
		void main() {
		   gl_FragColor = vec4(1,1,1,1);
		} """

def createGeometry():
	global geometry
	# create geometry
	dtype = [
		('position', np.float32, 3),
		('normal', np.float32, 3),
		('uv', np.float32, 2)
    ]
	geometry = np.zeros(5, dtype).view(gloo.VertexArray)
	geometry['position'] = [(-0.5, -0.5, 0.0),
	                    (-0.5, +0.5, 0.0),
	                    (+0.5, -0.5, 0.0),
	                    (+0.5, +0.5, 0.0),
	                    (+0.5, +0.5, 0.0)]


createShader()
createGeometry()

if __name__ == "__main__":


	# create entity
	quad = gloo.Program(vertexShader, fragmentShader)

	# create camera
	aspectRatio = 1.0
	projection = glm.perspective(45.0, aspectRatio, 0.1, 100.0)
	view = glm.lookAt( glm.vec3(2,2,-2), glm.vec3(0,0,0), glm.vec3(0,1,0) )
	
	# create transform
	model = np.eye(4, dtype=np.float32)
	
	# create window
	window = app.Window()

	def orbit(view, dx, dy):
		horizontalAxis = glm.vec3( view[0][0], view[1][0], view[2][0] )
		verticalAxis = glm.vec3(0,1,0)

		view *= glm.rotate(np.eye(4, dtype=np.float32), dy*0.006, horizontalAxis)
		view *= glm.rotate(np.eye(4, dtype=np.float32), dx*0.006, verticalAxis)

		return view

	@window.event
	def on_draw(dt):
		window.clear()
		# draw entity
		quad.bind(geometry)
		quad['projectionMatrix'] = projection	
		quad['viewMatrix'] = view
		quad['modelMatrix'] = model
		quad.draw(gl.GL_TRIANGLE_STRIP)

	@window.event
	def on_mouse_drag(x,y,dx,dy, buttons):
		global view
		view = orbit(view, dx, dy)

	app.run()
