#version 330 core

in vec3 FragPos;
in vec3 Normal;
uniform vec3 albedo;
uniform float roughness;
uniform float metallic;

layout (location = 0) out vec3 gPosition;
layout (location = 1) out vec3 gNormal;
layout (location = 2) out vec4 gAlbedoSpec;
layout (location = 3) out float gRoughness;
layout (location = 4) out float gMetallic;

void main(){
    gPosition = FragPos;
    gNormal = normalize(Normal);
    gAlbedoSpec.rgb = albedo;
    gAlbedoSpec.w = 1.0;
    gRoughness = roughness;
    gMetallic = metallic;
}