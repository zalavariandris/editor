from threading import Thread, RLock
from editor.render.window.glfw_window import GLFWWindow
from OpenGL.GL import *
import time
import numpy as np


class Window:
    def __init__(self):
        self.window = None
        self.clear_color = (0, 0, 0, 1)
        self.thread = None
        self.lock = None
        self.callbacks = {'init': [], 'tick': []}

    def start(self, threaded=False):
        if threaded:
            self.thread = Thread(target=self._start, daemon=True)
            self.lock = RLock()
            self.thread.start()
        else:
            self._start()

    def _start(self):
        self.window = GLFWWindow(1024, 768)
        with self.window:
            for f in self.callbacks['init']:
                f()
            while not self.window.should_close():
                with self.lock:
                    glClearColor(*self.clear_color)
                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    for f in self.callbacks['tick']:
                        f()
                    self.window.swap_buffers()
                    self.window.poll_events()
                    time.sleep(1/60)

    def on_init(self, f):
        self.callbacks['init'].append(f)

    def on_tick(self, f):
        self.callbacks['tick'].append(f)


if __name__ == "__main__":
    window = Window()

    @window.on_init
    def setup():
        pass

    @window.on_tick
    def draw():
        pass

    window.start(threaded=True)
    while True:
        time.sleep(0.3)
        with window.lock:
            window.clear_color = np.random.uniform(0, 1, (4,))
