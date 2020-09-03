#version 330 core

layout (location = 0) out vec3 gPosition;
layout (location = 1) out vec3 gNormal;
layout (location = 2) out vec4 gAlbedoSpec;

in vec2 TexCoords;
in vec3 WorldPos;
in vec3 Normal;

struct Material{
	vec3 albedo;
	float metallic;
	float roughness;
	float ao;
};

uniform Material material;

void main(){
	gPosition = WorldPos;
	gNormal = normalize(Normal);
	gAlbedoSpec.rgb = material.albedo.rgb;
	gAlbedoSpec.a = material.roughness;
}