#version 330 core
in vec2 vUv;
in vec3 FragPos;
in vec4 FragPosLightSpace;
in vec3 vNormal;

struct Material{
	sampler2D diffuseMap;
	sampler2D specularMap;
	samplerCube environmentMap;
};

struct DirectionalLight{
	sampler2D shadowMap;
	vec3 direction;

	vec3 ambient;
	vec3 diffuse;
	vec3 specular;
};

uniform Material material;
uniform DirectionalLight sun;

out vec4 color;
uniform vec3 cameraPos;

vec3 CalcDirLight(DirectionalLight light, vec3 normal, vec3 viewDir, vec3 ambientColor, vec3 diffuseColor, vec3 specularColor, float shiness){
	// ambient
	vec3 ambient = light.ambient * ambientColor;
	
	// diffuse
	vec3 norm = normalize(normal);
	vec3 lightDir = normalize(-light.direction);
	float diffuseStrength = 1.0;
	float diff = max(dot(normal, lightDir), 0.0);
	vec3 diffuse = light.diffuse * (diff * diffuseColor);

	// specular
	vec3 reflectDir = reflect(-lightDir, norm); 
	float spec = pow(max(dot(viewDir, reflectDir), 0.0), shiness);
	vec3 specular = light.specular * (spec * specularColor);  


	return ambient+diffuse+specular;
};

float ShadowCalculation(vec4 fragPosLightSpace, vec3 lightDir){
	// perform perspective divide
	vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;

	projCoords = projCoords*0.5+0.5;
	if(projCoords.z>1.0)
		return 0.0;

	float closestDepth = texture(sun.shadowMap, projCoords.xy).r;
	float currentDepth = projCoords.z;

	if(dot(vNormal, lightDir)<0.0)
	  return 0.0;

	float shadow = 0.0;
	float bias = max(0.005 * (1.0 - dot(vNormal, lightDir)), 0.005);
	bias = 0.005;
	vec2 texelSize = 1.0 / textureSize(sun.shadowMap, 0);
	for(int x = -1; x <= 1; ++x)
	{
	    for(int y = -1; y <= 1; ++y)
	    {
	        float pcfDepth = texture(sun.shadowMap, projCoords.xy + vec2(x, y) * texelSize).r; 
	        shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;        
	    }    
	}
	shadow /= 9.0;
	return shadow;
}

void main(){
	float IOR = 1.52;
	vec3 N = vNormal;
	vec3 I = normalize(FragPos-cameraPos); // view direction
	vec3 Rr = refract(I, normalize(N), 1.0/IOR); // refraction vector
	vec3 Rl = reflect(I, normalize(N)); // reflection vector
	vec3 tex = texture(material.diffuseMap, vUv).rgb;
	float shadow = ShadowCalculation(FragPosLightSpace, normalize(sun.direction));
	
	vec3 refraction = texture(material.environmentMap, Rr).rgb;
	vec3 reflection = texture(material.environmentMap, Rl).rgb;
	vec3 specular = texture(material.specularMap, vUv).rgb;

	color = vec4(tex*(1-shadow*0.8), 1.0);
}