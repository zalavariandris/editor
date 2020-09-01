#version 330 core

out vec4 color;
in vec2 TexCoords;
uniform sampler2D screenTexture;
uniform sampler2D bloomBlur;
uniform float exposure;
uniform float gamma=1.0;

void main(){
    vec3 hdrColor = texture(screenTexture, TexCoords).rgb;
    vec3 bloomColor = texture(bloomBlur, TexCoords).rgb;
    hdrColor+=bloomColor;
    
    // reinhardt tonemapping
    //vec3 mapped = hdrColor / (hdrColor+vec3(1.0));

    // exposure tone mapping
    vec3 mapped = vec3(1.0) - exp(-hdrColor * pow(2, exposure)); // FIXME: use f-stop, shutterspeed, aperturesize

    // gamma correction
    mapped = pow(mapped, vec3(1.0 / gamma));  

    color = vec4(mapped, 1.0);
}