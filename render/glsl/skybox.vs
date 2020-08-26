#version 330 core
layout (location = 0) in vec3 position;

out vec3 vUvw;

uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;

void main(){
	vUvw = position;
	vec4 pos = projectionMatrix * viewMatrix * vec4(position, 1.0);
	gl_Position = pos.xyww; // when usign glDepthFunc(GL_LEQUAL) it is visible and always farthest
}