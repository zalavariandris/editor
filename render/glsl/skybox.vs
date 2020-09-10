#version 330 core
layout (location = 0) in vec3 position;

out vec3 vUvw;

uniform mat4 projection;
uniform mat4 view;

void main(){
	vUvw = position;
	vec4 pos = projection * view * vec4(position, 1.0);
	gl_Position = pos.xyww; // when usign glDepthFunc(GL_LEQUAL) it is visible and always farthest
}