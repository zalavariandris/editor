#version 330 core
#define NUM_LIGHTS 3
#define NUM_SHADOWMAPS 2
#define NUM_SHADOWCUBES 1
const float PI = 3.14159265359;

uniform vec3 cameraPos;
uniform sampler2D gPosition;
uniform sampler2D gNormal;
uniform sampler2D gAlbedoSpecular;
uniform sampler2D gRoughness;
uniform sampler2D gMetallic;
uniform sampler2D gEmissive;

in vec2 TexCoords;
out vec4 FragColor;

struct Light{
	int type;
	vec3 color;
	vec3 position;
	vec3 direction;
	float cutOff;
	mat4 matrix;
	int shadowIdx;

	float nearPlane;
	float farPlane;
};

uniform Light lights[NUM_LIGHTS];
uniform sampler2D shadowMaps[NUM_SHADOWMAPS];
uniform samplerCube shadowCubes[NUM_SHADOWCUBES];
uniform samplerCube irradianceMap;
uniform samplerCube prefilterMap;
uniform sampler2D brdfLUT;

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

	// float bias = max(0.005 * (1.0 - dot(normal, lightDir)), 0.0005);
	float bias = 0.0001;
	float pcfDepth = texture(shadowMap, projCoords.xy).r; 
	float shadow = currentDepth - bias > pcfDepth ? 1.0 : 0.0;
	return shadow;
}

float PointShadowCalculation(vec3 lightPos, vec3 surfacePos, samplerCube shadowCubemap, float farPlane){
	vec3 L=surfacePos-lightPos;
	float shadowDepth = texture(shadowCubemap, normalize(L)).r;
	shadowDepth*=farPlane;

	float surfaceDepth = length(L);

	float bias = 0.1;
	float shadow = surfaceDepth > shadowDepth ? 1.0 : 0.0;

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

void main()
{
	// Pull geometry properties
	vec3 surfacePos = texture(gPosition, TexCoords).rgb;
	vec3 surfaceNormal = texture(gNormal, TexCoords).rgb;

	// Pull material properties
	vec3 albedo = texture(gAlbedoSpecular, TexCoords).rgb;
	float roughness = texture(gRoughness, TexCoords).r;
	float metallic = texture(gMetallic, TexCoords).r;
	float ao = 1.0;

	// Calculate lighting
	// ==================
	vec3 N = gl_FrontFacing ? normalize(surfaceNormal) : -normalize(surfaceNormal);
	vec3 V = normalize(cameraPos - surfacePos); //view vector
	vec3 R = reflect(-V, N);
	vec3 baseReflectivity = mix(vec3(0.04), albedo, metallic);

	// Reflectance equatation
	// ----------------------
	vec3 Lo=vec3(0);
	for(int i=0; i<NUM_LIGHTS; ++i)
	{
		// Calculate each light radiance
		// ----------------------------
		vec3 L=vec3(0);
		float attenuation=1.0;
		if(lights[i].type==0)
		{
			L = normalize(-lights[i].direction);
			attenuation=1.0;

			// calc shadow
			vec4 fragPosLightSpace = lights[i].matrix * vec4(surfacePos, 1.0);
			float shadow = ShadowCalculation(fragPosLightSpace, L, N, shadowMaps[lights[i].shadowIdx]);
			attenuation*=1-shadow;
		}
		else if(lights[i].type==1)
		{
			L = normalize(lights[i].position - surfacePos);
			float distance = length(lights[i].position - surfacePos);
			attenuation = 1.0 / (distance*distance);

			// spotlight cutoff
			if(lights[i].cutOff>=0)
			{
				float theta = dot(L, normalize(-lights[i].direction));
				if(theta<lights[i].cutOff){
					attenuation=0.0;
				}
			}

			// calc shadow
			vec4 fragPosLightSpace = lights[i].matrix * vec4(surfacePos, 1.0);
			float shadow = ShadowCalculation(fragPosLightSpace, L, N, shadowMaps[lights[i].shadowIdx]);
			attenuation*=1-shadow;
		}
		else if(lights[i].type==2){
			L = normalize(lights[i].position - surfacePos);
			float distance = length(lights[i].position - surfacePos);
			attenuation = 1.0 / (distance*distance);

			// calc shadow
			float shadow = PointShadowCalculation(lights[i].position, surfacePos, shadowCubes[0], lights[i].farPlane);
			attenuation*=1-shadow;
		}
		else{
			continue;
		}

		vec3 radiance = lights[i].color * attenuation;
		
		// Cook-Torrance BRDF, calcuate per-light surface luminance
		// ========================================================
		float diff = max(dot(N, L), 0.0);
		vec3 H = normalize(V+L); /* halfway bysecting vector */
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

		// calc surface luminance
		// ----------------------
		vec3 luminance = (kD * albedo / PI + specular) * radiance * NdotL;
		// accumulate
		Lo+=luminance;
	}

	// IBL ambient
	// -----------
	// # Diffuse component
	vec3 F = fresnelSchlickRoughness(max(dot(N, V), 0.0), baseReflectivity, roughness);
    vec3 kS = F;
    vec3 kD = 1.0 - kS;
    kD *= 1.0 - metallic;	  
    
    vec3 irradiance = texture(irradianceMap, N).rgb;
    vec3 diffuse      = irradiance * albedo;
    
    // # Specular component
    // sample both the pre-filter map and the BRDF lut and combine them together as per the Split-Sum approximation to get the IBL specular part.
    const float MAX_REFLECTION_LOD = 4.0;
    vec3 prefilteredColor = textureLod(prefilterMap, R,  roughness * MAX_REFLECTION_LOD).rgb;    
    vec2 brdf  = texture(brdfLUT, vec2(max(dot(N, V), 0.0), roughness)).rg;
    vec3 specular = prefilteredColor * (F * brdf.x + brdf.y);

    // combine diffuse and specular component lighting
    vec3 ambient = (kD * diffuse + specular) * ao;

	//
	vec3 color = Lo+ambient;

	FragColor = vec4(color, 1.0);
}