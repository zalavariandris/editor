#version 330 core
layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal;
layout (location = 2) in vec2 uv;

out vec3 FragPos;
out vec2 TexCoords;
out vec3 Normal;

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

void main()
{
    vec4 viewPos = viewMatrix * modelMatrix * vec4(position, 1.0);
    FragPos = viewPos.xyz; 
    TexCoords = uv;
    
    mat3 normalMatrix = transpose(inverse(mat3(viewMatrix * modelMatrix)));
    Normal = normalMatrix * normal;
    
    gl_Position = projectionMatrix * viewPos;
}