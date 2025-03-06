import sys
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

interactive_angle_x = 0.0
interactive_angle_y = 0.0
scale_factor = 1.0

wireframe_mode = False
front_is_ccw = True

def draw_cube():
    vertices = [
        [-1.0, -1.0, -1.0],
        [ 1.0, -1.0, -1.0],
        [ 1.0,  1.0, -1.0],
        [-1.0,  1.0, -1.0],
        [-1.0, -1.0,  1.0],
        [ 1.0, -1.0,  1.0],
        [ 1.0,  1.0,  1.0],
        [-1.0,  1.0,  1.0],
    ]
    faces = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [0, 1, 5, 4],
        [2, 3, 7, 6],
        [1, 2, 6, 5],
        [0, 3, 7, 4],
    ]

    glBegin(GL_QUADS)
    for face in faces:
        for v in face:
            glVertex3fv(vertices[v])
    glEnd()

    if not wireframe_mode:
        glDisable(GL_LIGHTING)
        glColor3f(0, 0, 0)
        glLineWidth(2.0)
        for face in faces:
            glBegin(GL_LINE_LOOP)
            for v in face:
                glVertex3fv(vertices[v])
            glEnd()
        glEnable(GL_LIGHTING)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glTranslatef(0.0, 0.0, -5.0)

    glRotatef(interactive_angle_x, 1, 0, 0)
    glRotatef(interactive_angle_y, 0, 1, 0)
    glScalef(scale_factor, scale_factor, scale_factor)

    glColor3f(0.0, 0.8, 0.0)
    draw_cube()

    glPushMatrix()
    glLoadIdentity()
    glTranslatef(2.5, 0.0, -5.0)
    glColor3f(0.8, 0.0, 0.0)
    draw_cube()
    glPopMatrix()

    glutSwapBuffers()

def keyboard(key, x, y):
    global scale_factor, wireframe_mode, interactive_angle_x, interactive_angle_y
    global front_is_ccw

    if isinstance(key, bytes):
        key = key.decode("utf-8", "ignore")

    if key == '+':
        scale_factor *= 1.1
    elif key == '-':
        scale_factor /= 1.1

    elif key.lower() == 'm':
        wireframe_mode = not wireframe_mode
        if wireframe_mode:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    elif key.lower() == 'f':
        front_is_ccw = not front_is_ccw
        if front_is_ccw:
            glFrontFace(GL_CCW)
        else:
            glFrontFace(GL_CW)

    elif key.lower() == 'r':
        interactive_angle_x = 0.0
        interactive_angle_y = 0.0
        scale_factor = 1.0

    elif key == '\x1b':
        sys.exit()

    glutPostRedisplay()

def special_keys(key, x, y):
    global interactive_angle_x, interactive_angle_y
    if key == GLUT_KEY_UP:
        interactive_angle_x += 5
    elif key == GLUT_KEY_DOWN:
        interactive_angle_x -= 5
    elif key == GLUT_KEY_LEFT:
        interactive_angle_y -= 5
    elif key == GLUT_KEY_RIGHT:
        interactive_angle_y += 5
    glutPostRedisplay()

def init():
    glClearColor(0.9, 0.9, 0.9, 1.0)  # Светлый фон
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    light_pos = [10.0, 10.0, 10.0, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glEnable(GL_MULTISAMPLE)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

def reshape(width, height):
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    aspect = width / float(height)
    if width <= height:
        glOrtho(-3, 3, -3/aspect, 3/aspect, 0.1, 100.0)
    else:
        glOrtho(-3*aspect, 3*aspect, -3, 3, 0.1, 100.0)

    angle_degs = 45.0
    scale = 0.5
    rad = math.radians(angle_degs)
    sx = -scale * math.cos(rad)
    sy = -scale * math.sin(rad)
    S = [
        1.0, 0.0, sx, 0.0,
        0.0, 1.0, sy, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    ]
    glMultMatrixf(S)

    glMatrixMode(GL_MODELVIEW)

def main():
    glutInit(sys.argv)
    glutInitDisplayString(b"samples=8 rgb double depth")
    glutInitWindowSize(800, 600)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Cube")

    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMainLoop()

if __name__ == "__main__":
    main()
