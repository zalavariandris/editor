#version 330 core
layout (location=0) in vec3 position;
layout (location=1) in vec2 uv;
layout (location=2) in vec3 normal;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

out vec3 FragPos;
out vec3 Normal;
out vec3 Albedo;
out float Specular;

void main(){
	// position in world-space
    FragPos = (model * vec4(position, 1.0)).xyz;

    // normal in word-space
    mat3 normalMatrix = transpose(inverse(mat3(model)));
	Normal = normalMatrix * normal;

	// albedo
	Albedo = vec3(0.8,0.3,0.3);

	// specular
	Specular = 0.3;

	// transform vertices 
    gl_Position = projection * view * model * vec4(position, 1.0);
}