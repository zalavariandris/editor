#version 330 core

out vec4 FragColor;
in vec2 TexCoords;
uniform sampler2D screenTexture;
uniform sampler2D bloomBlur;
uniform float exposure;
uniform float gamma=2.2;

void main(){
    vec3 hdrColor = texture(screenTexture, TexCoords).rgb;
    vec3 bloomColor = texture(bloomBlur, TexCoords).rgb;
    vec3 color=hdrColor+bloomColor;
    
    // reinhardt tonemapping
    // vec3 mapped = hdrColor / (hdrColor+vec3(1.0));

    // exposure tone mapping
    color = vec3(1.0) - exp(-hdrColor * pow(2, exposure)); // FIXME: use f-stop, shutterspeed, aperturesize

    // gamma correction
    color = pow(color, vec3(1.0 / gamma));  

    FragColor = vec4(color, 1.0);
}