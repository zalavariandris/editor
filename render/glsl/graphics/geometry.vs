#version 330 core
layout (location=0) in vec3 position;
layout (location=1) in vec2 uv;
layout (location=2) in vec3 normal;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

out vec3 Position;
out vec3 Normal;

out vec2 TexCoords;

void main(){
    TexCoords = uv;
	// position in world-space
    Position = (model * vec4(position, 1.0)).xyz;

    // normal in word-space
    mat3 normalMatrix = transpose(inverse(mat3( model)));
	Normal = normalMatrix * normal;

	// transform vertices
    gl_Position = projection * view * model * vec4(position, 1.0);
}