#version 330 core
out vec2 TexCoords;

layout (location = 0) in vec3 position;
layout (location = 1) in vec2 uv;

void main(){
    TexCoords = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
}