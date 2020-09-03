#version 330 core

struct Light{
	int type; //0: Directional, 1: Omni, 2: Spot
	vec3 position;
	vec3 direction;
	vec3 color;
};

 uniform sampler2D gPosition;
uniform sampler2D gNormal;
uniform sampler2D gAlbedoSpecular;

uniform Light lights[16];

in vec2 TexCoords;

out vec4 FragColor;
const float PI = 3.14159265359;

uniform vec3 cameraPos;
/* PBR HELPER FUNCTIONS*/

/*self shadowing microfacets*/
float distributionGGX(float NdotH, float roughness){
	float a = roughness * roughness;
	float a2 = a*a;
	float denom = NdotH * NdotH * (a2-1.0)+1.0;
	denom = PI * denom * denom;
	return a2 / max(denom, 0.0000001); 
}

/*rougness effect based on light and normnal angle*/
float geometrySmith(float NdotV, float NdotL, float roughness){
	float r = roughness + 1.0;
	float k = (r*r)/8.0;
	float ggx1 = NdotV / (NdotV * (1.0-k)+k);
	float ggx2 = NdotL / (NdotL * (1.0-k)+k);
	return ggx1 * ggx2;
}

vec3 fresnelSchlick(float cosTheta, vec3 F0)
{
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

vec3 fresnelSchlickRoughness(float HdotV, vec3 F0, float roughness){
	// base reflectivity in range 0 to 1
	// returns range to 1
	// increases as HdotV decreases (more reflectivity when surface viewd at larger angles)
	return F0 + (max(vec3(1.0 - roughness), F0) - F0) * pow(1.0 - HdotV, 5.0);
}

void main(){
	// fetch geometry
	vec3 fragPos = texture(gPosition, TexCoords).rgb;	
	vec3 normal = texture(gNormal, TexCoords).rgb;

	// fetch material properties
	vec3 albedo = vec3(0.7);
	float roughness = 0.3;
	float metallic = 0.0;


	// Calculate lighting
	// ==================

	// PBR direct lighting
	// -------------------
	vec3 N = gl_FrontFacing ? normalize(normal) : -normalize(normal);
	vec3 L = normalize(lights[0].position-fragPos);
	vec3 V = normalize(cameraPos - fragPos); //view vector
	vec3 R = reflect(-V, N);

	vec3 baseReflectivity = mix(vec3(0.04), albedo, metallic);

	// reflectance equation
	vec3 Lo = vec3(0.0);
	for(int i=0; i<3; ++i){
		// calculate per-light radiance
		vec3 L = lights[i].type == 0 ? normalize(-lights[i].direction) : normalize(lights[i].position - fragPos);
		vec3 H = normalize(V+L); /* halfway bysecting vector */
		float distance = lights[i].type==0 ? 1.0 : length(lights[i].position - fragPos);
		float attenuation = lights[i].type==0 ? 1.0 : 1.0 / (distance*distance);
		vec3 radiance = lights[i].color * attenuation;

		//Cook-Torrance BRDF
		float NdotV = max(dot(N, V), 0.0000001);
		float NdotL = max(dot(N, L), 0.0000001);
		float HdotV = max(dot(H, V), 0.0);
		float NdotH = max(dot(N, H), 0.0);

		float D = distributionGGX(NdotH, roughness); // larger the more micro-facets aligned to H
		float G = geometrySmith(NdotV, NdotL, roughness); // smaller the more microfacets shadowed by other micro-facets
		vec3 F = fresnelSchlick(HdotV, baseReflectivity); //proportion of specular reflectance

		vec3 specular = D * G * F;
		specular /= 4.0 * NdotV * NdotL;

		// for energy conservation, the diffuse and specular light cant
		// be above 1.0 (unless the surface emits light); to preserve this
		// relationship the diffuse component (kD) should equal 1.0-kS.
		// kD: diffuse component
		// Ks: specular component
		vec3 kD = vec3(1.0) - F; //F equals kS
		kD *= 1.0 - metallic;	

		// calc luminance
		vec3 luminance = (kD * albedo / PI + specular) * radiance * NdotL;

		Lo+=luminance; //output luminance
	}

	
	vec3 color = Lo;

	// PBR ambient
	// -----------



	// Output
	// ======
	FragColor = vec4(color, 1.0);
}