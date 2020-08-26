#version 330 core

out vec4 color;
in vec2 vUv;
uniform sampler2D screenTexture;

void main(){
    const float gamma = 2.2;
    vec3 hdrColor = texture(screenTexture, vUv).rgb;

    // reinhardt tonemapping
    //vec3 mapped = hdrColor / (hdrColor+vec3(1.0));

    // exposure tone mapping
    const float exposure = 1.0;
    vec3 mapped = vec3(1.0) - exp(-hdrColor * exposure); // FIXME: use f-stop, shutterspeed, aperturesize

    // gamma correction
    mapped = pow(mapped, vec3(1.0 / gamma));  

    color = vec4(mapped, 1.0);
}