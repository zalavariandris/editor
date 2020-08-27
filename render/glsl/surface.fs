#version 330 core
out vec4 color;
in vec2 TexCoords;
struct Material{
	sampler2D diffuseMap;
};
Material material;

void main(){
	vec3 col = texture(material.diffuseMap, TexCoords).rgb;
	color = vec4(col,1);
}