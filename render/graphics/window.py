import glfw
from threading import Thread, RLock
from OpenGL.GL import *
import functools

from editor.render import puregl
import glm


class Window:
    def __init__(self, width=1280, height=720, title="Graphics Viewer", background_color=(0,0,0,1), floating=False):
        self.width = width
        self.height = height
        self.title = title
        self.thread = None
        self.lock = None
        self.background_color = background_color
        self._floating = floating
        self._callbacks = {
            'setup': [],
            'draw': [],
            "mousemove": [],
            "mousebutton": [],
            'scroll': [],
            'resize': []
        }

        from editor.render.graphics import PerspectiveCamera
        self.camera = PerspectiveCamera(glm.mat4(1), glm.radians(39.6), self.width/self.height, 0.1, 30)
        self.camera.transform = glm.inverse(glm.lookAt(glm.vec3(2, 3, 6), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0)))

    def _create_window(self):
        # Initialize the library
        if not glfw.init():
            raise Exception("cant init glfw")

        # Create a windowed mode window and its OpenGL context
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.FLOATING, GL_TRUE if self._floating else GL_FALSE)
        self._handle = glfw.create_window(self.width, self.height, self.title, None, None)
        if not self._handle:
            glfw.terminate()
            raise Exception("cant create glfw window")

    def _setup_window_events(self):
        # Events
        glfw.set_input_mode(self._handle, glfw.STICKY_KEYS, True)  # FIXME: this migth be ueful later, when implementing keyboard events
        self._prev_mouse_pos = (-1, -1)

        # mouse
        prev_mouse_pos = (0, 0)

        @functools.partial(glfw.set_mouse_button_callback, self._handle)
        def mousebutton(handle, button, action, modifiers):
            nonlocal prev_mouse_pos
            self.mousebutton(button, action, modifiers)
            prev_mouse_pos = glfw.get_cursor_pos(self._handle)

        @functools.partial(glfw.set_cursor_pos_callback, self._handle)
        def mousemove(handle, x, y):
            self.mousemove(x-self._prev_mouse_pos[0], y-self._prev_mouse_pos[1])
            self._prev_mouse_pos = x, y

        glfw.set_scroll_callback(self._handle, lambda handle, dx, dy: self.scroll(dx, dy))
        glfw.set_window_size_callback(self._handle, lambda handle, w, h: self.resize(w, h))

    def scroll(self, dx, dy):
        s = 1 + dy / 10
        self.camera.position *= glm.vec3(1/s)
        for f in self._callbacks['scroll']:
            f(dx, dy)

    def mousemove(self, dx, dy):
        if glfw.get_mouse_button(self._handle, 0):
            self.camera.transform = glm.inverse(puregl.transform.orbit(glm.inverse(self.camera.transform), dx * 2, dy * 2))
        for f in self._callbacks['mousemove']:
            f(dx, dy)

    def mousebutton(self, button, action, modifiers):
        for f in self._callbacks["mousebutton"]:
            f(button, action, modifiers)

    def resize(self, width, height):
        self.camera.aspect = width/height
        glViewport(0, 0, width, height)
        for f in self._callbacks['resize']:
            f(width, height)

    def _start(self):
        self._create_window()
        self._setup_window_events()

        # Make the window's context current
        glfw.make_context_current(self._handle)

        # invoke callbacks
        self.setup()

        # Loop until the user closes the window
        while not glfw.window_should_close(self._handle):
            glClearColor(*self.background_color)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_DEPTH_TEST)
            # Render here, e.g. using pyOpenGL
            if self.lock:
                with self.lock:
                    self.draw()
            else:
                self.draw()

            # Swap front and back buffers
            glfw.swap_buffers(self._handle)

            # Poll for and process events
            glfw.poll_events()

        glfw.terminate()

    # public interface
    def start(self, worker=False):
        if worker:
            self.thread = Thread(target=self._start)
            self.lock = RLock()
            self.thread.start()
        else:
            self._start()

    def on_setup(self, f):
        self._callbacks['setup'].append(f)

    def setup(self):
        """by default invokes all on_setup callbacks"""
        for f in self._callbacks['setup']:
            f()

    def on_draw(self, f):
        self._callbacks['draw'].append(f)

    def draw(self):
        """by default invokes all on_draw callbacks"""
        for f in self._callbacks['draw']:
            glViewport(0, 0, self.width, self.height)
            f()


if __name__ == "__main__":
    from editor.render.graphics import Scene, Mesh, Geometry, Material
    import glm
    from editor.render import puregl, glsl

    cube = Mesh(transform=glm.translate(glm.mat4(1), (1, 0.5, 0.0)),
                geometry=Geometry(*puregl.geo.cube()),
                material=Material(albedo=(1, 0, 0),
                                  roughness=0.7,
                                  metallic=0.0))
    sphere = Mesh(transform=glm.translate(glm.mat4(1), (-1,0.5, 0.0)),
                  geometry=Geometry(*puregl.geo.sphere()),
                  material=Material(albedo=(0.04, 0.5, 0.8),
                                    roughness=0.2,
                                    metallic=1.0))
    plane = Mesh(transform=glm.translate(glm.mat4(1), (0, 0.0, 0.0)),
                 geometry=Geometry(*puregl.geo.plane()),
                 material=Material(albedo=(0.5, 0.5, 0.5),
                                   roughness=0.8,
                                   metallic=0.0))

    scene = Scene()
    scene.add_child(cube)
    scene.add_child(sphere)
    scene.add_child(plane)
    viewer = Window(floating=True)

    # confi viewer
    prog = None

    @viewer.on_setup
    def setup_scene():
        global prog
        # program
        prog = puregl.program.create(
            """#version 330 core
            uniform mat4 projection;
            uniform mat4 view;
            uniform mat4 model;
            
            layout (location=0) in vec3 position;
            layout (location=1) in vec3 normal;
            layout (location=2) in vec2 uv;
            
            out vec2 TexCoords;
            
            void main(){
                TexCoords = uv;
                gl_Position = projection * view * model * vec4(position, 1);
            }
            """,
            """#version 330 core
            uniform vec3 ambient;
            uniform vec3 diffuse;
            out vec4 FragColor;
            void main(){
                vec3 color = ambient + diffuse;
                FragColor = vec4(color,1);
            }
            """
        )

        # geometry
        for child in scene.children:
            child.geometry._setup()

    @viewer.on_draw
    def draw_scene():
        global prog
        # draw
        with puregl.program.use(prog):
            # camera
            puregl.program.set_uniform(prog, "projection", viewer.camera.projection)
            puregl.program.set_uniform(prog, "view", viewer.camera.view)

            for child in scene.children:
                # transform
                puregl.program.set_uniform(prog, "model", child.transform)

                # material
                puregl.program.set_uniform(prog, "ambient", glm.vec3(*child.material.albedo))

                # geometry
                child.geometry._draw(prog)

            # draw grid
            puregl.imdraw.grid(viewer.camera.projection, viewer.camera.view)
            puregl.imdraw.axis(viewer.camera.projection, viewer.camera.view)

    viewer.start(worker=True)
    print("- end of program -")
