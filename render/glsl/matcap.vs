#version 330 core
layout (location = 0) in vec3 position;
layout (location = 2) in vec3 normal;

uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;
uniform mat4 modelMatrix;

out vec3 Eye;
out vec3 Normal;

void main() {

	mat4 modelViewMatrix =  viewMatrix * modelMatrix;
	Eye = normalize( vec3( modelViewMatrix * vec4( position, 1.0 ) ) );
	mat3 normalMatrix = transpose(inverse(mat3(modelViewMatrix)));
	Normal = normalize( normalMatrix * normal );
	gl_PointSize = 5.0;
	gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4( position, 1.0 );
}