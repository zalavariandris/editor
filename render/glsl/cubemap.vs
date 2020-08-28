#version 330 core
layout (location = 0) in vec3 position;

out vec3 WorldPos;

uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;

void main()
{
    WorldPos = position;
    gl_Position =  projectionMatrix * viewMatrix * vec4(WorldPos, 1.0);
}