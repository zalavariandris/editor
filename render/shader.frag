#version 330 core
struct Material {
	vec3 ambient;
	vec3 diffuse;
	vec3 specular;
	float shiness;

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

vec3 CalcDirLight(DirectionalLight light, vec3 normal, vec3 viewDir){
	// ambient
	vec3 ambient = light.ambient * material.ambient;
	
	// diffuse
	vec3 norm = normalize(normal);
	vec3 lightDir = normalize(-light.direction);
	float diffuseStrength = 1.0;
	float diff = max(dot(normal, lightDir), 0.0);

	vec3 diffuseColor = material.diffuse;
	if(material.useDiffuseMap){
		diffuseColor = texture(material.diffuseMap, vUv).rgb;	
	}

	if(material.useVertexColor){
		diffuseColor*=vColor.rgb;
	}
	vec3 diffuse = light.diffuse * (diff * diffuseColor);

	// specular
	vec3 reflectDir = reflect(-lightDir, norm); 
	float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shiness);
	vec3 specularColor = material.specular;
	if(material.useSpecularMap){
		specularColor = texture(material.specularMap, vUv).rgb;
	}
	vec3 specular = light.specular * (spec * specularColor);  


	return ambient+diffuse+specular;
};

vec3 CalcPointLight(PointLight light, vec3 normal, vec3 fragPos, vec3 viewDir){
	// ambient
	vec3 ambient = light.ambient * material.ambient;
	
	// diffuse
	vec3 norm = normalize(normal);
	vec3 lightDir = normalize(light.position - fragPos);
	float diffuseStrength = 1.0;
	float diff = max(dot(normal, lightDir), 0.0);

	vec3 diffuseColor = material.diffuse;
	
	if(material.useDiffuseMap){
		diffuseColor = texture(material.diffuseMap, vUv).rgb;	
	}

	if(material.useVertexColor){
		diffuseColor*=vColor.rgb;
	}
	vec3 diffuse = light.diffuse * (diff * diffuseColor);

	// specular
	vec3 reflectDir = reflect(-lightDir, norm); 
	float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shiness);
	vec3 specularColor = material.specular;
	if(material.useSpecularMap){
		specularColor = texture(material.specularMap, vUv).rgb;
	}
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
		result += CalcDirLight(sun, vNormal, viewDir);
		for(int i=0; i<NR_POINT_LIGHTS;i++){
			result += CalcPointLight(pointLights[i], vNormal, fragPos, viewDir);
		};

		// send result
		color = vec4(result, 1);
	}