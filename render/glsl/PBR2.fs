#version 330 core
#define NUM_LIGHTS 3
#define NUM_SHADOWMAPS 2
#define NUM_SHADOWCUBES 1

uniform sampler2D gPosition;
uniform sampler2D gNormal;
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

void main()
{
	vec3 surfacePos = texture(gPosition, TexCoords).rgb;
	vec3 surfaceNormal = texture(gNormal, TexCoords).rgb;
	vec3 N = normalize(surfaceNormal);

	// lambert shading
	vec3 Lo=vec3(0);
	for(int i=0; i<NUM_LIGHTS; ++i)
	{
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

		vec3 radiance = lights[i].color * attenuation;
		
		// BRDF
		float diff = max(dot(N, L), 0.0);
		Lo+=diff*radiance;
	}
	vec3 color = Lo;

	FragColor = vec4(color, 1.0);
}