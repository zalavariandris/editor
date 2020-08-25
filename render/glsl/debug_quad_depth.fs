#version 330 core
in vec2 vUv;
uniform sampler2D depthMap;
out vec4 color;

void main(){
	float depthValue = texture(depthMap, vUv).r;
	color = vec4(vec3(depthValue), 1.0);
}