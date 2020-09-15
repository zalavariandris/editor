from OpenGL.GL import *
import time
import numpy as np
import glfw
import sys

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
    window = glfw.create_window(1024, 768, "WINDOW", None, None)
    if not window:
        sys.exit(2)

except GLError as err:
    raise err

glfw.make_context_current(window)

while not glfw.window_should_close(window):
    glClearColor(0, 0, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glfw.poll_events()
    time.sleep(1/60)



