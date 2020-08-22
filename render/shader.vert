#version 330 core
in vec3 position;
in vec3 normal;
in vec4 color;
in vec2 uv;

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

out vec4 vColor;
out vec2 vUv;
out vec3 vNormal;
out vec3 fragPos;
void main(){
	gl_PointSize=5.0;
	vColor = vec4(color.rgb, 1);
	vNormal = normalize(normal);
	vUv = uv;
	mat4 normalMatrix = transpose(inverse(modelMatrix)); //FIXME: calc on CPU and send as uniform
	fragPos = vec3(normalMatrix * vec4(position, 1.0));
	gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1);
}