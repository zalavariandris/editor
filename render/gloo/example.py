"""
used references:
- https://metamost.com/opengl-with-python/
"""

from OpenGL.GL import *
from OpenGL.error import GLError, NullFunctionError
import glm
import glfw
import contextlib
import sys
import ctypes
import numpy as np
from editor.render.helpers import orbit, plane, box, sphere
from editor.utils import profile
import functools
from pathlib import Path
from window import Window
from editor.render.gloo import Shader, VAO, VBO, EBO, Texture, FBO


if __name__ == '__main__':
    import math
    # variables
    width, height = 640, 480

    # matrices
    model_matrix = np.identity(4)
    view_matrix = glm.lookAt( glm.vec3(0, 1,4), glm.vec3(0,0.7,0), glm.vec3(0,1,0) )
    projection_matrix = glm.perspective(math.radians(60), width/height, 0.1, 100)

    #
    # Init Window
    #
    window = Window(width, height, (0, 0, 0.4, 1.0))

    @window.addEventListener("mousemove")
    def mousemove(x, y, dx, dy):
        global view_matrix
        if window.get_mouse_button(0):
            view_matrix = orbit(view_matrix, dx*2,dy*2)

    @window.addEventListener("mousebutton")
    def mousebutton(button, action, modifiers):
        pass

    @window.addEventListener("scroll")
    def scroll(dx, dy):
        global view_matrix
        s = 1+dy/10
        view_matrix = glm.scale(view_matrix, (s,s,s))

    @window.addEventListener("resize")
    def resize(w, h):
        global projection_matrix
        glViewport(0, 0, w, h)
        projection_matrix = glm.perspective(math.radians(60), w/h, 1, 100)

    #
    # Create Geometry
    #
    plane_geometry = plane(width=3, length=3)
    box_geometry = box(origin=(0,-0.5, 0))
    sphere_geometry = sphere(radius=0.5, origin=(0,-0.5,0))
    cctv_geometry = plane(1,1)

    # transform vertices to model position
    model = glm.mat4(1)
    model = glm.translate(model, glm.vec3(-0.7, 1.8, -0.5))
    model = glm.rotate(model, math.radians(60), glm.vec3(0, 1, 0))
    model = glm.rotate(model, math.radians(120), glm.vec3(1, 0, 0))
    model = glm.scale(model, glm.vec3(1, 1, 1))
    cctv_modelmatrix = model

    with window: # set gl contex to window
        #
        # Create GPU Geometry
        #
        box_bufferattributes = {
            'position': (VBO(box_geometry['positions']), 3),
            'normal':   (VBO(box_geometry['normals']),   3),
            'color':    (VBO(box_geometry['colors']),    4),
            'uv':       (VBO(box_geometry['uvs']),       2),
            'indices':  (EBO(box_geometry['indices']),    1)
        }

        plane_bufferattributes = {
            'position': (VBO(plane_geometry['positions']), 3),
            'normal':   (VBO(plane_geometry['normals']),   3),
            'color':    (VBO(plane_geometry['colors']),    4),
            'uv':       (VBO(plane_geometry['uvs']),       2),
            'indices':  (EBO(plane_geometry['indices']),    1)
        }

        cctv_bufferattributes = {
            'position': (VBO(cctv_geometry['positions']), 3),
            'normal':   (VBO(cctv_geometry['normals']),   3),
            'color':    (VBO(cctv_geometry['colors']),    4),
            'uv':       (VBO(cctv_geometry['uvs']),       2),
            'indices':  (EBO(cctv_geometry['indices']),    1)
        }

        # TODO: Single VBO with structured nparray
        Vertex = [('position', np.float32, 3),
                 ('normal',   np.float32, 3),
                 ('color',   np.float32, 3),
                 ('uv',   np.float32, 2)]

        vertices = np.zeros( 2, dtype=Vertex )
        print(vertices['position'])
        print(vertices['uv'])
        sphere_bufferattributes = {
            'position': (VBO(sphere_geometry['positions']), 3),
            'normal':   (VBO(sphere_geometry['normals']),   3),
            'color':    (VBO(sphere_geometry['colors']),    4),
            'uv':       (VBO(sphere_geometry['uvs']),       2),
            'indices':  (EBO(sphere_geometry['indices']),    1)
        }



        # 
        # Create Textures
        #

        # gradient texture
        gradient_data = np.ones( (64,64,3) ).astype(np.float32)
        xv, yv = np.meshgrid(np.linspace(0,1,64),np.linspace(0,1,64))
        gradient_data[:,:,0] = 1
        gradient_data[:,:,1] = xv.astype(np.float32)
        gradient_data[:,:,2] = yv.astype(np.float32)
        gradient_texture = Texture.from_data(gradient_data, slot=0)
        

        # noise texture
        noise_data = np.random.uniform( 0,1, (64,64,3)).astype(np.float32)
        noise_texture = Texture.from_data(noise_data, slot=0)
        
        # render to texture fbo
        fbo = FBO(640, 480, slot=3)

        #
        # Create entities
        #
        box_entity = {
            'attributes': box_bufferattributes,
            'transform': glm.translate(glm.mat4(1), glm.vec3(0.5, 0.0, 0)),
            'material':{
                'shader': Shader(Path('shader.vert').read_text(), Path('shader.frag').read_text()),
                'vao': VAO(),
                'uniforms':{
                    'material.diffuseMap': noise_texture
                }
            }
        }

        plane_entity = {
            'attributes': plane_bufferattributes,
            'transform': np.eye(4),
            'material':{
                'shader': Shader(Path('shader.vert').read_text(), Path('shader.frag').read_text()),
                'vao': VAO(),
                'uniforms':{
                    'material.diffuseMap': gradient_texture
                }
            }
        }

        cctv_entity = {
            'attributes': cctv_bufferattributes,
            'transform': cctv_modelmatrix,
            'material':{
                'shader': Shader(Path('shader.vert').read_text(), Path('shader.frag').read_text()),
                'vao': VAO(),
                'uniforms':{
                    'material.diffuseMap': fbo.texture
                }
                
            }
        }

        sphere_entity = {
            'attributes': sphere_bufferattributes,
            'transform': glm.translate(glm.mat4(1), glm.vec3(-0.5, 0.0, 0)),
            'material':{
                'shader': Shader(Path('shader.vert').read_text(), Path('shader.frag').read_text()),
                'vao': VAO(),
                'uniforms':{
                    'material.diffuseMap': noise_texture
                }
            }
        }

        scene = [plane_entity, box_entity, cctv_entity, sphere_entity]

        # START
        import time
        glEnable(GL_DEPTH_TEST)        
        while not window.should_close():
            with profile("draw", True):
                Window.poll_events()
                def draw_scene():
                    # draw each entity
                    for entity in scene:
                        with entity['material']['shader'] as shader, entity['material']['vao'] as vao:
                            # update uniforms
                            shader.set_uniform("useLights", False)
                            shader.set_uniform("viewMatrix", view_matrix)
                            shader.set_uniform("projectionMatrix", np.array(projection_matrix))
                            shader.set_uniform("modelMatrix", entity['transform'])
                            shader.set_uniform("material.useDiffuseMap", True)
                            viewPos = np.linalg.inv(view_matrix)[3][:3]
                            shader.set_uniform("viewPos", viewPos)


                            # set vao to geometry vbos
                            for name, attribute in entity['attributes'].items():
                                if name!='indices':
                                    vbo, size = attribute
                                    """Enable attributes for current vertex array in shader"""
                                    location = shader.get_attribute_location(name)
                                    vao.enable_vertex_attribute(location)

                                    # set attribute pointer in shader
                                    vao.set_vertex_attribute(location, vbo, size, GL_FLOAT)
                            
                            # draw object
                            indexBuffer = entity['attributes']['indices'][0]

                            texture = entity['material']['uniforms']['material.diffuseMap']
                            with indexBuffer:
                                count = indexBuffer.count
                                
                                shader.set_uniform("material.diffuseMap", texture.texture_unit)
                                if texture:
                                    with texture:
                                        shader.set_uniform("material.useDiffuseMap", True)
                                        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                                        glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
                                        shader.set_uniform("material.useDiffuseMap", False)
                                        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                                        glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
                                        glDrawElements(GL_POINTS, count, GL_UNSIGNED_INT, None)
                                else:
                                    shader.set_uniform("useDiffuseMap", True)
                                    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                                    glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
                                    shader.set_uniform("useDiffuseMap", False)
                                    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                                    glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, None)
                                    glDrawElements(GL_POINTS, count, GL_UNSIGNED_INT, None)

                glEnable( GL_PROGRAM_POINT_SIZE )
                with fbo:
                    glViewport(0, 0, fbo.width, fbo.height)
                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    draw_scene()

                glViewport(0, 0, window.width, window.height)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                draw_scene()

                window.swap_buffers()

                

