#version 330 core
out vec4 FragColor;

struct Material{
	vec3 albedo;
	float metallic;
	float roughness;
	float ao;
};

uniform Material material;

//lights
struct Light{
	vec3 direction;
	vec3 position;
	vec3 color;
};

uniform Light light;
uniform vec3 cameraPos;

// IBL
uniform samplerCube irradianceMap;
uniform samplerCube prefilterMap;
uniform sampler2D brdfLUT;

uniform sampler2D shadowMap;


const float PI = 3.14159265359;

in vec2 TexCoords;
in vec3 WorldPos;
in vec3 Normal;
in vec4 FragPosLightSpace;

/**/
float ShadowCalculation(vec4 fragPosLightSpace, vec3 lightDir, vec3 normal, sampler2D shadowMap){
	// perform perspective divide
	vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;

	projCoords = projCoords*0.5+0.5;
	if(projCoords.z>1.0)
		return 0.0;

	float closestDepth = texture(shadowMap, projCoords.xy).r;
	float currentDepth = projCoords.z;

	if(dot(normal, lightDir)<0.0)
	  return 0.0;

	float shadow = 0.0;
	float bias = max(0.05 * (1.0 - dot(normal, lightDir)), 0.005);
	// bias = 0.05;
	vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
	for(int x = -1; x <= 1; ++x)
	{
	    for(int y = -1; y <= 1; ++y)
	    {
	        float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize).r; 
	        shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;        
	    }    
	}
	shadow /= 9.0;
	return shadow;
}

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
	vec3 N = normalize(Normal);
	vec3 V = normalize(cameraPos - WorldPos); //view vector
	vec3 R = reflect(-V, N); 

	// calculate reflectance at normal incidence; if dia-electric (like plastic) use baseReflectivity
	// of 0.04 and if it's a metal, use the albedo color as baseReflectivity (metallic workflow)
	vec3 baseReflectivity/*F0*/ = mix(vec3(0.04), material.albedo, material.metallic);

	// reflectance equation
	vec3 Lo = vec3(0.0);
	
	for(int i=0; i<1; i++){
		// calculate per-light radiance
		vec3 L = normalize(light.position - WorldPos);
		vec3 H = normalize(V+L); /* halfway bysecting vector */
		float distance = 1.0;//length(light.position - WorldPos);
		float attenuation = 1.0 / (distance*distance);
		vec3 radiance = light.color * attenuation;

		//Cook-Torrance BRDF
		float NdotV = max(dot(N, V), 0.0000001);
		float NdotL = max(dot(N, L), 0.0000001);
		float HdotV = max(dot(H, V), 0.0);
		float NdotH = max(dot(N, H), 0.0);

		float D = distributionGGX(NdotH, material.roughness); // larger the more micro-facets aligned to H
		float G = geometrySmith(NdotV, NdotL, material.roughness); // smaller the more microfacets shadowed by other micro-facets
		vec3 F = fresnelSchlick(HdotV, baseReflectivity); //proportion of specular reflectance

		vec3 specular = D * G * F;
		specular /= 4.0 * NdotV * NdotL;

		// for energy conservation, the diffuse and specular light cant
		// be above 1.0 (unless the surface emits light); to preserve this
		// relationship the diffuse component (kD) should equal 1.0-kS.
		// kD: diffuse component
		// Ks: specular component
		vec3 kD = vec3(1.0) - F; //F equals kS
		kD *= 1.0 - material.metallic;	

		float shadow = ShadowCalculation(FragPosLightSpace, L, N, shadowMap);
		Lo+=(kD * material.albedo / PI + specular) * radiance * NdotL * (1-shadow); //output luminance
		
	}

	// ambient lighting (we now use IBL as the ambient term)
    vec3 F = fresnelSchlickRoughness(max(dot(N, V), 0.0), baseReflectivity, material.roughness);
    
    vec3 kS = F;
    vec3 kD = 1.0 - kS;
    kD *= 1.0 - material.metallic;	  
    
    vec3 irradiance = texture(irradianceMap, N).rgb;
    vec3 diffuse      = irradiance * material.albedo;
    
    // sample both the pre-filter map and the BRDF lut and combine them together as per the Split-Sum approximation to get the IBL specular part.
    const float MAX_REFLECTION_LOD = 4.0;
    vec3 prefilteredColor = textureLod(prefilterMap, R,  material.roughness * MAX_REFLECTION_LOD).rgb;    
    vec2 brdf  = texture(brdfLUT, vec2(max(dot(N, V), 0.0), material.roughness)).rg;
    vec3 specular = prefilteredColor * (F * brdf.x + brdf.y);

    vec3 ambient = (kD * diffuse + specular) * material.ao;
    
    vec3 color = ambient + Lo;

	FragColor = vec4(color, 1.0);
}