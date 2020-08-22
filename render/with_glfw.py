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
from editor.render.helpers import orbit, plane, box, sphere, profile

import functools
from pathlib import Path

class Window:
    def __init__(self, width, height, clear_color=(0,0,0,1)):
        # attributes
        self._clear_color = clear_color
        
        # gl context and window
        if not glfw.init():
            sys.exit(1)

        try:
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

            title = "Window"

            # create window
            self._handle = glfw.create_window(width, height, title, None, None)
            if not self._handle:
                sys.exit(2)

        except GLError as err:
            raise err

        # Events
        glfw.set_input_mode(self._handle, glfw.STICKY_KEYS, True) #FIXE: this migth be ueful later, when implementing keyboard events
        self._callbacks = {"mousemove": [], "mousebutton": [], 'scroll':[], 'resize':[]}

        # mouse
        prev_mouse_pos = (0,0)
        @functools.partial(glfw.set_cursor_pos_callback, self._handle)
        def mousemove(handle, x, y):
            nonlocal prev_mouse_pos
            for callback in self._callbacks["mousemove"]:
                callback(x,y,x-prev_mouse_pos[0],y-prev_mouse_pos[1])
            prev_mouse_pos = x,y

        @functools.partial(glfw.set_mouse_button_callback, self._handle)
        def mousebutton(handle, button, action, modifiers):
            nonlocal prev_mouse_pos
            for callback in self._callbacks["mousebutton"]:
                callback(button, action, modifiers)
            prev_mouse_pos = glfw.get_cursor_pos(self._handle)

        @functools.partial(glfw.set_scroll_callback, self._handle)
        def scroll(handle, dx, dy):
            for callback in self._callbacks['scroll']:
                callback(dx, dy)

        @functools.partial(glfw.set_window_size_callback, self._handle)
        def resize(handle, width, height):
            for callback in self._callbacks['resize']:
                self._width, self._height = width, height
                callback(width, height)

        self._width, self._height = width, height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def __enter__(self):
        glfw.make_context_current(self._handle)
        glClearColor(*self._clear_color)
        
        return self

    def __exit__(self, type, value, traceback):
        pass
        # glfw.destroy_window(self._handle)

    def destroy(self):
        glfw.destroy_window(self._handle)

    def __del__(self):
         #FIXME: delete occurs after window handle is not valid
        glfw.terminate()

    def should_close(self):
        return glfw.window_should_close(self._handle)

    def get_mouse_button(self, button):
        return glfw.get_mouse_button(self._handle, button)

    """ attach event handlers """
    def addEventListener(self, event, function=None):
        """
        Attach an event handlers to events.

        can also be used as a decorator
        like so:
        @addEventListener("mousemove")
        def myMousemoveCallback(x, y)
        """

        if function is not None:
            # used directly
            self._callbacks[event].append(function)
        else:
            # used as a decorator
            return functools.partial(self.addEventListener, event)

    def swap_buffers(self):
        glfw.swap_buffers(self._handle)

    @staticmethod
    def poll_events():
        glfw.poll_events()

from editor.render.gloo import Shader, VAO, VertexBuffer, IndexBuffer, Texture, FBO


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
            'position': (VertexBuffer(box_geometry['positions']), 3),
            'normal':   (VertexBuffer(box_geometry['normals']),   3),
            'color':    (VertexBuffer(box_geometry['colors']),    4),
            'uv':       (VertexBuffer(box_geometry['uvs']),       2),
            'indices':  (IndexBuffer(box_geometry['indices']),    1)
        }

        plane_bufferattributes = {
            'position': (VertexBuffer(plane_geometry['positions']), 3),
            'normal':   (VertexBuffer(plane_geometry['normals']),   3),
            'color':    (VertexBuffer(plane_geometry['colors']),    4),
            'uv':       (VertexBuffer(plane_geometry['uvs']),       2),
            'indices':  (IndexBuffer(plane_geometry['indices']),    1)
        }

        cctv_bufferattributes = {
            'position': (VertexBuffer(cctv_geometry['positions']), 3),
            'normal':   (VertexBuffer(cctv_geometry['normals']),   3),
            'color':    (VertexBuffer(cctv_geometry['colors']),    4),
            'uv':       (VertexBuffer(cctv_geometry['uvs']),       2),
            'indices':  (IndexBuffer(cctv_geometry['indices']),    1)
        }

        sphere_bufferattributes = {
            'position': (VertexBuffer(sphere_geometry['positions']), 3),
            'normal':   (VertexBuffer(sphere_geometry['normals']),   3),
            'color':    (VertexBuffer(sphere_geometry['colors']),    4),
            'uv':       (VertexBuffer(sphere_geometry['uvs']),       2),
            'indices':  (IndexBuffer(sphere_geometry['indices']),    1)
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

                

