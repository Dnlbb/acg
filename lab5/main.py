import sys
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

window_width, window_height = 800, 600
clicks = []
clipped_segments = []

rect = {'xmin':0, 'xmax':0, 'ymin':0, 'ymax':0}
stage = 0

EPSILON = 1.0

def classify_trivial(p1, p2):
    x1, y1 = p1; x2, y2 = p2
    if x1 < rect['xmin'] and x2 < rect['xmin']:
        return True

    if x1 > rect['xmax'] and x2 > rect['xmax']:
        return True

    if y1 < rect['ymin'] and y2 < rect['ymin']:
        return True
    if y1 > rect['ymax'] and y2 > rect['ymax']:
        return True
    return False

def midpoint_clip(p1, p2):
    x1, y1 = p1; x2, y2 = p2

    if (rect['xmin'] <= x1 <= rect['xmax'] and rect['ymin'] <= y1 <= rect['ymax'] and
        rect['xmin'] <= x2 <= rect['xmax'] and rect['ymin'] <= y2 <= rect['ymax']):
        return []


    if classify_trivial(p1, p2):
        return [(p1, p2)]

    if ((x2 - x1)**2 + (y2 - y1)**2)**0.5 < EPSILON:
        return [(p1, p2)]

    xm = 0.5 * (x1 + x2)
    ym = 0.5 * (y1 + y2)
    segs1 = midpoint_clip((x1, y1), (xm, ym))
    segs2 = midpoint_clip((xm, ym), (x2, y2))
    return segs1 + segs2

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glPointSize(5)

    if stage >= 1:
        glColor3f(0.2, 0.8, 0.2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(rect['xmin'], rect['ymin'])
        glVertex2f(rect['xmin'], rect['ymax'])
        glVertex2f(rect['xmax'], rect['ymax'])
        glVertex2f(rect['xmax'], rect['ymin'])
        glEnd()

    if stage >= 2:
        x1,y1 = clicks[2]; x2,y2 = clicks[3]
        glColor3f(0.2, 0.2, 0.8)
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(1, 0xF0F0)
        glBegin(GL_LINES)
        glVertex2f(x1,y1)
        glVertex2f(x2,y2)
        glEnd()
        glDisable(GL_LINE_STIPPLE)

        glColor3f(0.8, 0.1, 0.1)
        glBegin(GL_LINES)
        for (pa, pb) in clipped_segments:
            glVertex2f(*pa)
            glVertex2f(*pb)
        glEnd()

    glutSwapBuffers()

def mouse(button, state, x, y):
    global stage, clipped_segments
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        yy = window_height - y
        clicks.append((x, yy))

        if stage == 0 and len(clicks) == 2:
            x1,y1 = clicks[0]; x2,y2 = clicks[1]
            rect['xmin'], rect['xmax'] = min(x1,x2), max(x1,x2)
            rect['ymin'], rect['ymax'] = min(y1,y2), max(y1,y2)
            stage = 1

        elif stage == 1 and len(clicks) == 4:
            p1, p2 = clicks[2], clicks[3]
            clipped_segments = midpoint_clip(p1, p2)
            stage = 2

        glutPostRedisplay()

def keyboard(key, x, y):
    global clicks, stage, clipped_segments
    if key == b'r':

        clicks = []
        clipped_segments = []
        stage = 0
        glutPostRedisplay()
    elif key == b'\x1b':
        sys.exit(0)

def reshape(w, h):
    global window_width, window_height
    window_width, window_height = w, h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    gluOrtho2D(0, w, 0, h)
    glMatrixMode(GL_MODELVIEW)

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"2D Midpoint Clipping (External)")
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse)
    glutKeyboardFunc(keyboard)

    glClearColor(1,1,1,1)
    glutMainLoop()

if __name__ == '__main__':
    main()
