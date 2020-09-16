# API V1 =========================
def setup():
    # init stuff
    setup_geometry_pass()
    setup_lighting_pass()


def draw():
    # draw stuff
    draw_geometry_pass()
    draw_lighting_pass()


def start():
    viewer = Viewer()
    viewer.setup()
    with viewer:
        setup()
        while not viewer.should_close():
            draw()
            viewer.swap_buffers()
            viewer.poll_events()


thread = Thread(target=start)
thread.start()

# API V2 =========================
viewer = Viewer()
@viewer.on_setup
def setup_geometry_pass():
    pass

@viewer.on_tick
def draw_geometry_pass():
    pass

@viewer.on_setup
def setup_lighting_pass():
    pass

@viewer.on_tick
def draw_lighting_pass():
    pass

viewer.start(worker=True)

# API V2 =========================
class MyViewer(Viewer):
    def setup(self):
        super().setup()

    def draw(self):
        super().draw() # does nothing
        pass

    def on_mousemove(self):
        super().on_mousemove()
        pass

    def resize(self):
        super().resize()
        pass

