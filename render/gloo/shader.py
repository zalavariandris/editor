from OpenGL.GL import *
import numpy as np
import glm
import sys;
import glfw

class Shader:
		def __init__(self):
				shaders = {
						GL_VERTEX_SHADER: """
								#version 330 core
								in vec3 position;
								in vec3 normal;
								in vec4 color;
								in vec2 uv;

								uniform mat4 modelMatrix;
								uniform mat4 viewMatrix;
								uniform mat4 projectionMatrix;

								out vec4 vColor;
								out vec2 vUv;
								out vec3 vNormal;
								out vec3 fragPos;
								void main(){
									gl_PointSize=5.0;
									vColor = vec4(color.rgb, 1);
									vNormal = normalize(normal);
									vUv = uv;
									mat4 normalMatrix = transpose(inverse(modelMatrix)); //FIXME: calc on CPU and send as uniform
									fragPos = vec3(normalMatrix * vec4(position, 1.0));
									gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position, 1);
								}""",

						GL_FRAGMENT_SHADER: """
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
									float attenuation = 1.0 / (light.constant + light.linear * distance + 
    		    light.quadratic * (distance * distance));  
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
								"""
						}
				
				# FIXME: check for a valid contex
				# and throw an error before using gl commands
				self.program_id = glCreateProgram()

				try:
						self.shader_ids = []
						for shader_type, shader_src in shaders.items():
								shader_id = glCreateShader(shader_type)
								glShaderSource(shader_id, shader_src)

								glCompileShader(shader_id)

								# check if compilation was successful
								result = glGetShaderiv(shader_id, GL_COMPILE_STATUS)
								info_log_len = glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH)
								if info_log_len:
										logmsg = glGetShaderInfoLog(shader_id)
										print(logmsg)
										sys.exit(10)

								glAttachShader(self.program_id, shader_id)
								self.shader_ids.append(shader_id)

						glLinkProgram(self.program_id)

						# check if linking was successful
						result = glGetProgramiv(self.program_id, GL_LINK_STATUS)
						info_log_len = glGetProgramiv(self.program_id, GL_INFO_LOG_LENGTH)
						if info_log_len:
								logmsg = glGetProgramInfoLog(self.program_id)
								print(logmsg)
								sys.exit(11)

						
				except Exception as err:
						raise err

		def __enter__(self):
				glUseProgram(self.program_id)
				return self

		def __exit__(self, type, value, traceback):
				glUseProgram(0)

		def __del__(self):
				for shader_id in self.shader_ids:
						glDetachShader(self.program_id, shader_id)
						glDeleteShader(shader_id)
				glDeleteProgram(self.program_id)
				print("delete shader program")

		def get_uniform_location(self, name):
				location = glGetUniformLocation(self.program_id, name)
				assert location>=0
				return location

		def set_uniform(self, name, value: [np.ndarray, int, glm.mat4x4]):
				location = self.get_uniform_location(name)

				if isinstance(value, np.ndarray):
						if value.shape == (4, 4): # matrix
								glUniformMatrix4fv(location, 1, False, value)
						elif value.shape == (3,):
								glUniform3f(location, value[0], value[1], value[2])
						else:
								raise NotImplementedError('uniform {} {}'.format(type(value), value.shape))
				
				elif isinstance(value, glm.mat4x4):
						glUniformMatrix4fv(location, 1, False, np.array(value))
				elif isinstance(value, glm.vec3):
						glUniform3f(location, value.x, value.y, value.z)

				elif isinstance(value, tuple):
					if len(value)==3:
						glUniform3f(location, value[0], value[1], value[2])

				elif isinstance(value, bool):
						glUniform1i(location, value)
				elif isinstance(value, int):
						glUniform1i(location, value)
				elif isinstance(value, float):
						glUniform1f(location, value)
				else:
						raise NotImplementedError(type(value))

		def get_attribute_location(self, attribute_name):
				assert self.program_id == glGetIntegerv(GL_CURRENT_PROGRAM)
				return glGetAttribLocation(self.program_id, attribute_name)
