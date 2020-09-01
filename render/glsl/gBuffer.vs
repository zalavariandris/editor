#version 330 core

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;
uniform mat3 normalMatrix;

uniform mat4 lightSpaceMatrix; //FIXME: multiple lights

layout (location = 0) in vec3 position;
layout (location = 1) in vec2 uv;
layout (location = 2) in vec3 normal;

out vec2 TexCoords;
out vec3 WorldPos;
out vec3 Normal;
out vec4 FragPosLightSpace;

void main(){
	WorldPos = vec3(modelMatrix * vec4(position, 1.0));
	FragPosLightSpace = lightSpaceMatrix * vec4(WorldPos, 1.0);
	Normal = normalMatrix*normal;
	TexCoords = uv;

	gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1.0);
}