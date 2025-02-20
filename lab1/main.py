import glfw
import numpy as np
import OpenGL.GL as gl
import math

rotation_angle = 0.0

def key_callback(window, key, scancode, action, mods):
    global rotation_angle
    if key == glfw.KEY_SPACE and action == glfw.PRESS:
        rotation_angle += 10

def draw_star():
    global rotation_angle

    vertices = []
    num_points = 7
    radius_outer = 0.5
    radius_inner = 0.2

    for i in range(num_points * 2):
        angle = math.pi / 2 - (i * math.pi / num_points)
        r = radius_outer if i % 2 == 0 else radius_inner
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        vertices.append((x, y))

    vertices = np.array(vertices, dtype=np.float32)

    gl.glPushMatrix()
    gl.glRotatef(rotation_angle, 0, 0, 1)

    # Заливка звезды
    gl.glBegin(gl.GL_TRIANGLES)
    gl.glColor3f(1.0, 0.5, 0.0)

    for i in range(len(vertices)):
        gl.glVertex2f(0, 0)
        gl.glVertex2f(vertices[i][0], vertices[i][1])
        gl.glVertex2f(vertices[(i + 1) % len(vertices)][0], vertices[(i + 1) % len(vertices)][1])

    gl.glEnd()

    gl.glBegin(gl.GL_LINE_LOOP)
    gl.glColor3f(1.0, 1.0, 1.0)

    for v in vertices:
        gl.glVertex2f(v[0], v[1])

    gl.glEnd()

    gl.glPopMatrix()

def main():
    if not glfw.init():
        return

    window = glfw.create_window(600, 600, "7-конечная звезда", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)
    glfw.set_key_callback(window, key_callback)

    while not glfw.window_should_close(window):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glLoadIdentity()

        draw_star()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()
