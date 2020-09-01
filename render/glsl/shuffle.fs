#version 330 core
in vec2 TexCoords;
uniform sampler2D tex;
out vec4 FragColor;

struct Channels{
	int red;
	int green;
	int blue;
	int alpha;
};
uniform Channels shuffle;

void main(){
	vec4 color = texture(tex, TexCoords).rgba;
	FragColor = vec4(shuffle.red  >=0 ? color[shuffle.red]   : 0.0, 
		             shuffle.green>=0 ? color[shuffle.green] : 0.0, 
		             shuffle.blue >=0 ? color[shuffle.blue]  : 0.0, 
		             shuffle.alpha>=0 ? color[shuffle.alpha] : 1.0);
}