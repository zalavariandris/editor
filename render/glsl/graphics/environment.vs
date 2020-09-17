#version 330 core
layout (location = 0) in vec3 position;

out vec3 SurfacePos;

uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;

void main()
{
    SurfacePos = position;
    gl_Position =  projectionMatrix * viewMatrix * vec4(SurfacePos, 1.0);
}

