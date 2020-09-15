import glfw
import sys

def main(title=__file__):
    # Initialize the library
    if not glfw.init():
        sys.exit(1)
    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(640, 480, title, None, None)
    if not window:
        glfw.terminate()
        sys.exit(2)

    # Make the window's context current
    glfw.make_context_current(window)

    # Loop until the user closes the window
    while not glfw.window_should_close(window):
        # Render here, e.g. using pyOpenGL

        # Swap front and back buffers
        glfw.swap_buffers(window)

        # Poll for and process events
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    from threading import Thread, RLock
    thread = Thread(target=main, daemon=False)
    thread.start()
    print("boom")
