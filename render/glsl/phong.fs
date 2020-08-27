#version 330 core
in vec2 TexCoords;
in vec3 FragPos;
in vec4 FragPosLightSpace;
in vec3 Normal;

struct Material{
	sampler2D diffuseMap;
	sampler2D specularMap;
	samplerCube environmentMap;
	float shiness;
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

vec3 CalcDirLight(vec3 ambientColor, 
	              vec3 diffuseColor, 
	              vec3 specularColor, 
	              float shiness, 
	              DirectionalLight light, 
	              vec3 normal, 
	              vec3 viewDir, 
	              vec4 fragPosLightSpace){
	// ambient
	vec3 ambient = light.ambient * ambientColor;
	
	// diffuse
	vec3 lightDir = normalize(light.direction);
	vec3 norm = normalize(normal);
	float diff = max(dot(norm, lightDir), 0.0);
	vec3 diffuse = diffuseColor*diff*light.diffuse;

	// specular
	vec3 reflectDir = reflect(-lightDir, normal); 
	float spec = pow(max(dot(viewDir, reflectDir), 0.0), pow(2, shiness));
	vec3 specular = light.specular * (spec * specularColor); // FIXME: specular seem to be off on planar surfaces

	float shadow = ShadowCalculation(fragPosLightSpace, lightDir, normal, light.shadowMap);

	return ambient+(diffuse+specular)*(1-shadow);
}

void main(){
	vec3 I = normalize(cameraPos-FragPos); // view direction
	vec3 ambientColor = texture(material.diffuseMap, TexCoords).rgb;
	vec3 diffuseColor = texture(material.diffuseMap, TexCoords).rgb;
	vec3 specularColor = texture(material.specularMap, TexCoords).rgb;
	float shiness = material.shiness;
	vec3 col = CalcDirLight(ambientColor, 
				            diffuseColor, 
				            specularColor, 
				            shiness, 
				            sun, 
				            normalize(Normal), 
				            I, 
				            FragPosLightSpace);
	color = vec4(col, 1.0);
}