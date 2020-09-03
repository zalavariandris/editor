#version 330 core

in vec3 FragPos;
in vec3 Normal;
in vec3 Albedo;
in float Specular;

layout (location = 0) out vec3 gPosition;
layout (location = 1) out vec3 gNormal;
layout (location = 2) out vec4 gAlbedoSpec;

void main(){
    gPosition = FragPos;
    gNormal = normalize(Normal);
    gAlbedoSpec.rgb = vec3(0.5,0,0);
    gAlbedoSpec.w = 1.0;
}