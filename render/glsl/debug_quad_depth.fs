#version 330 core
in vec2 vUv;
uniform sampler2D tex;
out vec4 FragColor;

void main(){
	vec3 color = texture(tex, vUv).rgb;
	FragColor = vec4(vec3(color), 1.0);
}