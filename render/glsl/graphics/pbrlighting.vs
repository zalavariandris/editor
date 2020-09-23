#version 330 core
layout (location=0) in vec3 position;
layout (location=1) in vec2 uv;
uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;
uniform mat4 modelMatrix;

out vec2 TexCoords;

void main(){
	TexCoords = uv;
	gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
}