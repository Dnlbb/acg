from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import sys

R = 1.0
r = 0.3
n_major = 100
n_minor = 60
twist = 0.0

angle = 0.0


def compute_vertex(u, v):
    v_twisted = v + twist * u
    x = (R + r * math.cos(v_twisted)) * math.cos(u)
    y = (R + r * math.cos(v_twisted)) * math.sin(u)
    z = r * math.sin(v_twisted)

    cx = R * math.cos(u)
    cy = R * math.sin(u)
    cz = 0

    nx = x - cx
    ny = y - cy
    nz = z - cz
    norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if norm != 0:
        nx /= norm
        ny /= norm
        nz /= norm
    return (x, y, z), (nx, ny, nz)


def display():
    global angle
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    gluLookAt(3, 3, 3, 0, 0, 0, 0, 1, 0)

    glRotatef(angle, 0.0, 1.0, 0.0)

    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    for i in range(n_major):
        for j in range(n_minor):
            i_next = (i + 1) % n_major
            j_next = (j + 1) % n_minor

            u = 2 * math.pi * i / n_major
            u_next = 2 * math.pi * i_next / n_major
            v = 2 * math.pi * j / n_minor
            v_next = 2 * math.pi * j_next / n_minor

            vertex1, normal1 = compute_vertex(u, v)
            vertex2, normal2 = compute_vertex(u_next, v)
            vertex3, normal3 = compute_vertex(u_next, v_next)
            vertex4, normal4 = compute_vertex(u, v_next)

            glNormal3f(*normal1)
            glVertex3f(*vertex1)

            glNormal3f(*normal2)
            glVertex3f(*vertex2)

            glNormal3f(*normal3)
            glVertex3f(*vertex3)

            glNormal3f(*normal4)
            glVertex3f(*vertex4)
    glEnd()

    glutSwapBuffers()

    angle = (angle + 0.5) % 360


def reshape(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, float(width) / height, 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def keyboard(key, x, y):
    if key == b'\x1b':
        sys.exit()


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Tor")
    glEnable(GL_DEPTH_TEST)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glShadeModel(GL_SMOOTH)

    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 50.0)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutIdleFunc(display)

    glutMainLoop()


if __name__ == "__main__":
    main()
