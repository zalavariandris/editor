#version 330 core
in vec2 vUv;
in vec3 FragPos;
in vec4 FragPosLightSpace;
in vec3 vNormal;

vec3 albedoColor;
bool useAlbedoMap;
uniform sampler2D albedoMap;
float metalnessValue;
bool useMetalnessMap;
uniform sampler2D metalnessMap;
float roughnessValue;
bool iseRoughnessMap;
uniform sampler2D roughnessMap;
vec3 emissionColor;
bool useEmissionMap;
uniform sampler2D emissionMap;
uniform sampler2D shadowMap;

out vec4 color;
uniform vec3 lightDir;

float ShadowCalculation(vec4 fragPosLightSpace, vec3 lightDir){
	// perform perspective divide
	vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;

	projCoords = projCoords*0.5+0.5;
	if(projCoords.z>1.0)
		return 0.0;

	float closestDepth = texture(shadowMap, projCoords.xy).r;
	float currentDepth = projCoords.z;

	if(dot(vNormal, lightDir)<0.0)
	  return 0.0;

	float shadow = 0.0;
	float bias = max(0.005 * (1.0 - dot(vNormal, lightDir)), 0.005);
	bias = 0.005;
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

void main(){
	vec3 tex = texture(albedoMap, vUv).rgb;
	float shadow = ShadowCalculation(FragPosLightSpace, normalize(lightDir));
	color = vec4(tex*(1-shadow*0.8), 1.0);
}