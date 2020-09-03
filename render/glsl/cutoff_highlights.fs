#version 330 core

uniform sampler2D screenTexture;
in vec2 TexCoords;
out vec4 BrightColor;

void main(){
	vec4 fragColor = texture(screenTexture, TexCoords);

	float brightness = dot(fragColor.rgb, vec3(0.2126, 0.7152, 0.0722));
	if(brightness>1.0){
		BrightColor = vec4(fragColor.rgb, 1.0);
	}else{
		BrightColor = vec4(0.0,0.0,0.0,1.0);
	}
}