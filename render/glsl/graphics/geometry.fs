#version 330 core

layout (location = 0) out vec3 gPosition;
layout (location = 1) out vec3 gNormal;

layout (location = 2) out vec3 gAlbedo;
layout (location = 3) out vec3 gEmission;
layout (location = 4) out float gRoughness;
layout (location = 5) out float gMetallic;

in vec2 TexCoords;

in vec3 Position;
in vec3 Normal;

uniform vec3 albedo;
uniform vec3 emission;
uniform float roughness;
uniform float metallic;

void main(){
	gPosition = Position;
	gNormal = normalize(Normal);
	gAlbedo = albedo;
	gEmission = emission;
	gRoughness = roughness;
	gMetallic = metallic;
}