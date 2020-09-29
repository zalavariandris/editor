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
    vec4 fragPosLightSpace = light.matrix * vec4(surfacePosition, 1.0);
    vec3 L = -normalize(light.direction);
    if(dot(L, surfaceNormal)<=0){
        return 0.0;
    }
    // perform perspective divide
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;

    projCoords = projCoords*0.5+0.5;
    if(projCoords.z>1.0)
        return 0.0;

    float shadowDepth = texture(light.shadowMap, projCoords.xy).r;
    float surfaceDepth = projCoords.z;

    // float bias = max(0.005 * (1.0 - dot(normal, L)), 0.0005);
    float bias = 0.0001;
    float shadow = surfaceDepth - bias > shadowDepth ? 1.0 : 0.0;        
}

/*DirectionalLight*/
vec3 calcRadiance(DirectionalLight light){
    return light.color * light.intensity;
}

float calcShadow(DirectionalLight light, vec3 surfacePosition, vec3 surfaceNormal){
    vec4 fragPosLightSpace = light.matrix * vec4(surfacePosition, 1.0);
    vec3 L = -normalize(light.direction);
    if(dot(L, surfaceNormal)<=0){
        return 0.0;
    }
    // perform perspective divide
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;

    projCoords = projCoords*0.5+0.5;
    if(projCoords.z>1.0)
        return 0.0;

    float shadowDepth = texture(light.shadowMap, projCoords.xy).r;
    float surfaceDepth = projCoords.z;

    // float bias = max(0.005 * (1.0 - dot(normal, L)), 0.0005);
    float bias = 0.0001;
    float shadow = surfaceDepth - bias > shadowDepth ? 1.0 : 0.0;        


    return shadow;
}

/*
 * Shading
 */
uniform vec3 cameraPos;
const float PI = 3.14159265359;
struct PBRMaterial{
   vec3 albedo;
   vec3 emission;
   float roughness;
   float metallic;
   float ao;
};
uniform PBRMaterial material;

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

vec3 calcCookTorranceBRDF(PBRMaterial material, vec3 N, vec3 L, vec3 V, vec3 radiance){
    vec3 baseReflectivity = mix(vec3(0.04), material.albedo, material.metallic);
    // Cook-Torrance BRDF, calcuate per-light surface luminance
    // ========================================================
    float diff = max(dot(N, L), 0.0);
    vec3 H = normalize(V+L); /* halfway bysecting vector */
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

    // calc surface luminance
    // ----------------------
    vec3 reflectance = (kD * material.albedo / PI + specular) * radiance * NdotL;
    return reflectance;
}

vec3 calcLambertBRDF(PBRMaterial material, vec3 N, vec3 L, vec3 radiance){
    float NdotL = max(dot(N, L), 0.0000001);
    vec3 reflectance = max(NdotL,0.0)*radiance;
    return reflectance*material.albedo;
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
    vec3 V = normalize(cameraPos - surfacePosition); //view vector

    vec3 Lo=vec3(0);
    {
        for(int i=0; i<num_point_lights; i++){
            vec3 L = normalize( point_lights[i].position-surfacePosition);
            vec3 radiance = calcRadiance(point_lights[i], surfacePosition);
            float shadow = calcShadow(point_lights[i], surfacePosition, N);
            vec3 reflectance = calcCookTorranceBRDF(material, N, L, V, radiance*(1-shadow));
            Lo+=reflectance;
        }

        for(int i=0; i<num_spot_lights; i++){
            vec3 L = normalize(spot_lights[i].position-surfacePosition);
            vec3 radiance = calcRadiance(spot_lights[i], surfacePosition);
            float shadow = calcShadow(spot_lights[i], surfacePosition, N);
            vec3 reflectance = calcCookTorranceBRDF(material, N, L, V, radiance*(1-shadow));
            Lo+=reflectance;
        }

        for(int i=0; i<num_dir_lights; i++){
            vec3 L = -normalize(dir_lights[i].direction);
            vec3 radiance = calcRadiance(dir_lights[i]);
            float shadow = calcShadow(dir_lights[i], surfacePosition, N);
            vec3 reflectance = calcCookTorranceBRDF(material, N, L, V, radiance*(1-shadow));
            Lo+=reflectance;
        }
    }

    vec3 color = Lo;

    // gamma correction
    // exposure tone mapping
    color = color / (color + vec3(1.0));
    color = pow(color, vec3(1.0/2.2)); 

    FragColor = vec4(color, 1.0);
}