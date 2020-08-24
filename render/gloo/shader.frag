#version 330 core
struct Material {
	vec3 ambient;
	vec3 diffuse;
	vec3 specular;
	float shiness;

	bool useLights;

	bool useDiffuseMap;
	sampler2D diffuseMap;

	bool useSpecularMap;
	sampler2D specularMap;

	bool useVertexColor;
};

struct DirectionalLight{
	vec3 ambient;
	vec3 diffuse;
	vec3 specular;

	vec3 direction;
};

struct PointLight{
	vec3 ambient;
	vec3 diffuse;
	vec3 specular;

	vec3 position;

	float constant;
	float linear;
	float quadratic;
};

struct SpotLight{
	vec3 position;
	vec3 direction;

	vec3 ambient;
	vec3 diffuse;
	vec3 specular;

	float constant;
	float linear;
	float quadratic;
};


in vec4 vColor;
in vec2 vUv;
in vec3 vNormal;
in vec3 fragPos;
uniform vec3 viewPos;
uniform Material material;

#define NR_POINT_LIGHTS 1
uniform PointLight pointLights[NR_POINT_LIGHTS];
uniform DirectionalLight sun;

uniform bool useLights;

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

vec3 CalcPointLight(PointLight light, vec3 normal, vec3 fragPos, vec3 viewDir, vec3 ambientColor, vec3 diffuseColor, vec3 specularColor, float shiness){
	// ambient
	vec3 ambient = light.ambient * ambientColor;
	
	// diffuse
	vec3 norm = normalize(normal);
	vec3 lightDir = normalize(light.position - fragPos);
	float diffuseStrength = 1.0;
	float diff = max(dot(normal, lightDir), 0.0);

	vec3 diffuse = light.diffuse * (diff * diffuseColor);

	// specular
	vec3 reflectDir = reflect(-lightDir, norm); 
	float spec = pow(max(dot(viewDir, reflectDir), 0.0), shiness);
	vec3 specular = light.specular * (spec * specularColor);  


	// attenuation
	float distance    = length(light.position - fragPos);
	float attenuation = 1.0 / (light.constant + light.linear * distance + light.quadratic * (distance * distance));  
	ambient*=attenuation;
	diffuse*=attenuation;
	specular*=attenuation;
	return ambient+diffuse+specular;
};

out vec4 color;
void main(){
	/* Lighting */

	vec3 result = vec3(0.0);
	vec3 viewDir = normalize(viewPos - fragPos);

	vec3 ambientColor = material.ambient;
	vec3 diffuseColor = material.useDiffuseMap ? texture(material.diffuseMap, vUv).rgb : material.diffuse;
	if(material.useVertexColor) diffuseColor*=vColor.rgb;
	vec3 specularColor = material.useSpecularMap ? texture(material.specularMap, vUv).rgb : material.specular;

	if(useLights){
		result += CalcDirLight(sun, vNormal, viewDir, ambientColor, diffuseColor, specularColor, material.shiness);
		for(int i=0; i<NR_POINT_LIGHTS;i++){
			result += CalcPointLight(pointLights[i], vNormal, fragPos, viewDir, ambientColor, diffuseColor, specularColor, material.shiness);
		};
	}else{
		result=ambientColor+diffuseColor+specularColor;
	}

	// send result
	color = vec4(result, 1);
}