#version 330 core

layout (location=0) in vec3 position;
layout (location=1) in vec2 uv;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;



out vec2 TexCoords;



void main(){
	TexCoords = uv;
	vec3 worldPos = (model * vec4(position, 1.0)).xyz;
	gl_Position = projection * view * model * vec4(position, 1.0);
}