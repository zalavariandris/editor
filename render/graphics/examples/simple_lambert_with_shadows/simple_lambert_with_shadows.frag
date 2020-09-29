#version 330 core

/*
 * Lighting
 */
#define MAX_POINT_LIGHTS 3
#define MAX_SPOT_LIGHTS 3
#define MAX_DIR_LIGHTS 3

uniform struct PointLight{
    vec3 color;
    float intensity;
    vec3 position;
    samplerCube shadowcube;
    float farPlane;
};
uniform PointLight point_lights[MAX_POINT_LIGHTS];
uniform int num_point_lights;

uniform struct SpotLight{
    vec3 color;
    float intensity;
    vec3 position;
    vec3 direction;
    float cutOff;
    sampler2D shadowMap;
    mat4 matrix;
};
uniform SpotLight spot_lights[MAX_SPOT_LIGHTS];
uniform int num_spot_lights;

uniform struct DirectionalLight{
    vec3 color;
    float intensity;
    vec3 direction;
    sampler2D shadowMap;
    mat4 matrix;
};
uniform DirectionalLight dir_lights[MAX_DIR_LIGHTS];
uniform int num_dir_lights;

/*PointLight*/
vec3 calcRadiance(PointLight light, vec3 surfacePosition){
    vec3 lightPosition = light.position;
    vec3 L = normalize(lightPosition-surfacePosition);
    float dist = length(lightPosition-surfacePosition);
    float attenuation = 1.0 / (dist*dist);
    vec3 radiance = light.color * light.intensity * attenuation;

    return radiance;
}

float calcShadow(PointLight light, vec3 surfacePosition, vec3 surfaceNormal){
    vec3 L = normalize(light.position - surfacePosition);
    float dist = length(light.position - surfacePosition);
    // mask radiance with shadowmap
    float shadowDepth = texture(light.shadowcube, normalize(-L)).r*light.farPlane;
    float surfaceDepth = dist;
    float bias = 0.01;
    float shadow = surfaceDepth-bias > shadowDepth ? 1.0 : 0.0;
    return shadow;
}

/*SpotLight*/
vec3 calcRadiance(SpotLight light, vec3 surfacePosition){
    vec3 L = normalize(light.position - surfacePosition);
    float distance = length(light.position - surfacePosition);
    float attenuation = 1.0 / (distance*distance);

    // spotlight cutoff
    if(light.cutOff>=0)
    {
        float theta = dot(L, normalize(-light.direction));
        if(theta<light.cutOff){
            attenuation=0.0;
        }
    }

    // calc result
    vec3 radiance = light.color * light.intensity * attenuation;
    return radiance;
}

float calcShadow(SpotLight light, vec3 surfacePosition, vec3 surfaceNormal){
    vec3 L = -normalize(light.direction);
    vec4 fragPosLightSpace = light.matrix * vec4(surfacePosition, 1.0);
    if(dot(L, surfaceNormal)<=0){
        return 0.0;
    }
    // perform perspective divide
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;

    projCoords = projCoords*0.5+0.5;
    if(projCoords.z>1.0)
        return 0.0;

    float closestDepth = texture(light.shadowMap, projCoords.xy).r;
    float currentDepth = projCoords.z;

    // float bias = max(0.005 * (1.0 - dot(surfaceNormal, lightDir)), 0.0005);
    float bias = 0.00001;
    // PCF

    float shadow = currentDepth - bias > closestDepth ? 1.0 : 0.0;        
    return shadow;
}

/*DirectionalLight*/
vec3 calcRadiance(DirectionalLight light){
    return light.color * light.intensity;
}

float calcShadow(DirectionalLight light, vec3 surfacePosition, vec3 surfaceNormal){
    vec3 L = -normalize(light.direction);
    vec4 fragPosLightSpace = light.matrix * vec4(surfacePosition, 1.0);
    if(dot(L, surfaceNormal)<=0){
        return 0.0;
    }
    // perform perspective divide
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;

    projCoords = projCoords*0.5+0.5;
    if(projCoords.z>1.0)
        return 0.0;

    float closestDepth = texture(light.shadowMap, projCoords.xy).r;
    float currentDepth = projCoords.z;

    // float bias = max(0.005 * (1.0 - dot(surfaceNormal, lightDir)), 0.0005);
    float bias = 0.00001;
    // PCF

    float shadow = currentDepth - bias > closestDepth ? 1.0 : 0.0;        
    return shadow;
}

/*
 * Shading
 */
struct LambertMaterial{
   vec3 diffuse;
};
uniform LambertMaterial material;

vec3 calcLambertBRDF(LambertMaterial material, vec3 N, vec3 L, vec3 radiance){
    float NdotL = max(dot(N, L), 0.0000001);
    vec3 reflectance = max(NdotL,0.0)*radiance;
    return reflectance*material.diffuse;
}

/*
 * MainFunction
 */
uniform vec3 color;
in vec3 Position;
in vec3 Normal;
out vec4 FragColor;
void main(){
    vec3 N = normalize(Normal);
    vec3 surfacePosition = Position;

    vec3 Lo=vec3(0);
    {
        for(int i=0; i<num_point_lights; i++){
            vec3 L = normalize( point_lights[i].position-surfacePosition);
            vec3 radiance = calcRadiance(point_lights[i], surfacePosition);
            float shadow = calcShadow(point_lights[i], surfacePosition, N);
            vec3 reflectance = calcLambertBRDF(material, N, L, radiance*(1-shadow));
            Lo+=reflectance;
        }

        for(int i=0; i<num_spot_lights; i++){
            vec3 L = normalize(spot_lights[i].position-surfacePosition);
            vec3 radiance = calcRadiance(spot_lights[i], surfacePosition);
            float shadow = calcShadow(spot_lights[i], surfacePosition, N);
            vec3 reflectance = calcLambertBRDF(material, N, L, radiance*(1-shadow));
            Lo+=reflectance;
        }

        for(int i=0; i<num_dir_lights; i++){
            vec3 L = -normalize(dir_lights[i].direction);
            vec3 radiance = calcRadiance(dir_lights[i]);
            float shadow = calcShadow(dir_lights[i], surfacePosition, N);
            vec3 reflectance = calcLambertBRDF(material, N, L, radiance*(1-shadow));
            Lo+=reflectance;
        }
    }
    float ambient = 0.1;
    FragColor = vec4(ambient+Lo, 1.0);
}