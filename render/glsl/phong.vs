#version 330 core
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 uv;
layout (location = 3) in vec3 normal;

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;
uniform mat4 lightSpaceMatrix;

out vec2 vUv;
out vec3 vNormal;
out vec3 FragPos;
out vec4 FragPosLightSpace;

void main(){
	gl_PointSize = 5.0;
	vUv = uv;
	vNormal = normal;
	FragPos = vec3(modelMatrix * vec4(position, 1.0));
	FragPosLightSpace = lightSpaceMatrix * vec4(FragPos, 1.0);
	gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1);
}
