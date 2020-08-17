import pyglet



class HelloWorldWindow(pyglet.window.Window):
    def __init__(self):
        super(HelloWorldWindow, self).__init__(vsync=True)

        self.label = pyglet.text.Label('Hello, world!')

    def on_draw(self):
        self.clear()
        vertex_list = pyglet.graphics.vertex_list(
            2,
            ('v2i/dynamic', (10, 15, 30, 35)),
            ('c3B/static', (0, 0, 255, 0, 255, 0))
        )

        vertex_list.draw(pyglet.gl.GL_POINTS)

if __name__ == '__main__':
    window = HelloWorldWindow()
    pyglet.app.run()
