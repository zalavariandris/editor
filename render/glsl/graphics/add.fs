#version 330 core
uniform sampler2D inputA;
uniform sampler2D inputB;
in vec2 TexCoords;
out vec4 FragColor;

void main(){
	vec3 colorA = texture(inputA, TexCoords).rgb;
	vec3 colorB = texture(inputB, TexCoords).rgb;
	FragColor = vec4(colorA+colorB, 1.0);
}