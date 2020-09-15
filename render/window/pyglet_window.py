import pyglet
from pathlib import Path

from threading import Thread, RLock

f = Path("../assets/container2_axis.png").resolve()
print(f)

import math
import time
class Viewer:
    def __init__(self):
        self.render_lock = RLock()
        self.pos = (0,0)
        self.speed = 1.0
        self.radius = 100.0

    def setup(self):
        self.window = pyglet.window.Window()
        self.image = pyglet.image.load(str(f))

        def update(dt):
            pass
            # self.pos = math.sin(time.time()*self.speed)*self.radius, 0

        pyglet.clock.schedule_interval(update, 1/60)

        @self.window.event
        def on_draw():
            self.render_lock.acquire()
            self.window.clear()
            self.image.blit(*self.pos)
            self.render_lock.release()

    def start(self):
        self.setup()
        pyglet.app.run()

viewer = Viewer()

thread = Thread(target=viewer.start)
thread.start()
