#version 330 core

layout (location = 0) in vec3 position;
layout (location = 1) in vec2 uv;
layout (location = 2) in vec3 normal;

out vec3 ViewPos;
out vec2 TexCoords;
out vec3 ViewNormal;

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

void main(){
	ViewPos = (viewMatrix * modelMatrix * vec4(position, 1.0)).xyz;
	TexCoords = uv;

	mat3 normalMatrix = transpose(inverse(mat3(viewMatrix*modelMatrix)));
	ViewNormal = mat3(viewMatrix) * normalMatrix * normal;

}