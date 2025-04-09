import glfw
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
import sys
import math
import ctypes

INITIAL_WIN_WIDTH = 800
INITIAL_WIN_HEIGHT = 600 #
CLEAR_COLOR_FLOAT = (0.1, 0.1, 0.1, 1.0)
CLEAR_COLOR_UINT8 = tuple(int(c * 255) for c in CLEAR_COLOR_FLOAT[:3])
FILL_COLOR_RGB = (0, 50, 155)
LINE_COLOR_RGB = (255, 255, 0)
MARKER_COLOR_RGB = (255, 0, 0)


class EdgeBucket:
    def __init__(self, y_max, x_at_y_min, slope_inv):
        self.y_max = y_max
        self.x = x_at_y_min
        self.slope_inv = slope_inv
    def __lt__(self, other):
        return self.x < other.x


def draw_pixel(buffer, x, y, color_rgb):
    h, w, _ = buffer.shape
    x_int, y_int = int(round(x)), int(round(y))
    if 0 <= x_int < w and 0 <= y_int < h:
        buffer[y_int, x_int] = color_rgb

def _get_background_color(buffer, x, y):
    h, w, _ = buffer.shape
    x_int, y_int = int(math.floor(x)), int(math.floor(y))
    if 0 <= x_int < w and 0 <= y_int < h:
        return buffer[y_int, x_int]
    return CLEAR_COLOR_UINT8

def _blend_colors(fg_rgb, bg_rgb, intensity):
    fg = np.array(fg_rgb, dtype=np.float32)
    bg = np.array(bg_rgb, dtype=np.float32)
    blended = fg * intensity + bg * (1.0 - intensity)
    return np.clip(blended, 0, 255).astype(np.uint8)

def draw_pixel_aa(buffer, x, y, intensity, line_color_rgb):
    h, w, _ = buffer.shape
    x_int, y_int = int(math.floor(x)), int(math.floor(y))
    if 0 <= x_int < w and 0 <= y_int < h:
        bg_color = buffer[y_int, x_int].copy()  # Копируем цвет фона
        blended_color = _blend_colors(line_color_rgb, bg_color, intensity)
        buffer[y_int, x_int] = blended_color

def filter(buffer, x0, y0, x1, y1, color_rgb):
    def ipart(x): return math.floor(x)
    def round_half_up(x): return ipart(x + 0.5)
    def fpart(x): return x - math.floor(x)
    def rfpart(x): return 1.0 - fpart(x)

    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0, x1, y1 = y0, x0, y1, x1
    if x0 > x1:
        x0, x1, y0, y1 = x1, x0, y1, y0

    dx = x1 - x0
    dy = y1 - y0
    gradient = dy / dx if dx != 0.0 else 1.0

    xend = round_half_up(x0)
    yend = y0 + gradient * (xend - x0)
    xgap = rfpart(x0 + 0.5)
    xpxl1 = int(xend)
    ypxl1 = ipart(yend)

    if steep:
        draw_pixel_aa(buffer, ypxl1,     xpxl1, rfpart(yend) * xgap, color_rgb)
        draw_pixel_aa(buffer, ypxl1 + 1, xpxl1,  fpart(yend) * xgap, color_rgb)
    else:
        draw_pixel_aa(buffer, xpxl1, ypxl1,     rfpart(yend) * xgap, color_rgb)
        draw_pixel_aa(buffer, xpxl1, ypxl1 + 1,  fpart(yend) * xgap, color_rgb)
    intery = yend + gradient

    xend = round_half_up(x1)
    yend = y1 + gradient * (xend - x1)
    xgap = fpart(x1 + 0.5)
    xpxl2 = int(xend)
    ypxl2 = ipart(yend)

    if steep:
        draw_pixel_aa(buffer, ypxl2,     xpxl2, rfpart(yend) * xgap, color_rgb)
        draw_pixel_aa(buffer, ypxl2 + 1, xpxl2,  fpart(yend) * xgap, color_rgb)
    else:
        draw_pixel_aa(buffer, xpxl2, ypxl2,     rfpart(yend) * xgap, color_rgb)
        draw_pixel_aa(buffer, xpxl2, ypxl2 + 1,  fpart(yend) * xgap, color_rgb)

    if steep:
        for x in range(xpxl1 + 1, xpxl2):
            draw_pixel_aa(buffer, ipart(intery),     x, rfpart(intery), color_rgb)
            draw_pixel_aa(buffer, ipart(intery) + 1, x,  fpart(intery), color_rgb)
            intery += gradient
    else:
        for x in range(xpxl1 + 1, xpxl2):
            draw_pixel_aa(buffer, x, ipart(intery),     rfpart(intery), color_rgb)
            draw_pixel_aa(buffer, x, ipart(intery) + 1,  fpart(intery), color_rgb)
            intery += gradient

def draw_horizontal_line(buffer, y, x_start, x_end, color_rgb):
    h, w, _ = buffer.shape
    y_int = int(round(y))
    if 0 <= y_int < h:
        if x_start > x_end:
            x_start, x_end = x_end, x_start
        x_start_int = max(0, int(round(x_start)))
        x_end_int = min(w, int(round(x_end)) + 1)
        if x_start_int < x_end_int:
            buffer[y_int, x_start_int:x_end_int] = color_rgb


VERTEX_SHADER_SRC = """
#version 330 core
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoord;

out vec2 TexCoord;

void main()
{
    gl_Position = vec4(aPos, 0.0, 1.0);
    TexCoord = aTexCoord;
}
"""

FRAGMENT_SHADER_SRC = """
#version 330 core
out vec4 FragColor;

in vec2 TexCoord;

// Текстура, содержащая наш буфер
uniform sampler2D screenTexture;

void main()
{
    FragColor = texture(screenTexture, TexCoord);
}
"""

def fill_polygon_scanline(buffer, vertices, color_rgb):
    if not vertices or len(vertices) < 3:
        return
    h, w, _ = buffer.shape
    y_coords = [v[1] for v in vertices]
    y_min_poly = int(round(min(y_coords)))
    y_max_poly = int(round(max(y_coords)))
    scan_y_start = max(0, y_min_poly)
    scan_y_end = min(h, y_max_poly + 1)
    if scan_y_start >= scan_y_end:
        return

    edge_table = {y: [] for y in range(scan_y_start, scan_y_end)}
    num_vertices = len(vertices)
    for i in range(num_vertices):
        p1, p2 = vertices[i], vertices[(i + 1) % num_vertices]
        x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]
        if round(y1) == round(y2):
            continue
        if y1 < y2:
            y_min_edge, y_max_edge, x_at_y_min = y1, y2, x1
        else:
            y_min_edge, y_max_edge, x_at_y_min = y2, y1, x2
            x1, x2, y1, y2 = x2, x1, y2, y1
        slope_inv = (x2 - x1) / (y2 - y1) if (y2 - y1) != 0 else 0.0
        y_min_int = int(round(y_min_edge))
        actual_y_start = max(scan_y_start, y_min_int)
        if actual_y_start < scan_y_end and y_max_edge > actual_y_start:
            x_adjusted = x_at_y_min + slope_inv * (actual_y_start - y_min_edge)
            edge = EdgeBucket(y_max_edge, x_adjusted, slope_inv)
            if actual_y_start in edge_table:
                edge_table[actual_y_start].append(edge)

    active_edge_table = []
    for y in range(scan_y_start, scan_y_end):
        active_edge_table = [edge for edge in active_edge_table if y < round(edge.y_max)]
        if y in edge_table:
            active_edge_table.extend(edge_table[y])
        active_edge_table.sort(key=lambda edge: edge.x)
        for i in range(0, len(active_edge_table) - 1, 2):
            x_start, x_end = active_edge_table[i].x, active_edge_table[i+1].x
            draw_horizontal_line(buffer, y, x_start, x_end, color_rgb)
        for edge in active_edge_table:
            edge.x += edge.slope_inv

class AppState:
    def __init__(self, fb_width, fb_height):
        self.fb_width = fb_width
        self.fb_height = fb_height
        self.buffer = None
        self.vertices = []
        self.needs_buffer_update = True
        self.create_buffer()

    def create_buffer(self):
        self.buffer = np.zeros((self.fb_height, self.fb_width, 3), dtype=np.uint8)
        self.buffer[:, :] = CLEAR_COLOR_UINT8
        print(f"Framebuffer buffer created/resized: {self.fb_width}x{self.fb_height}")
        self.needs_buffer_update = True

    def clear_all(self):
        self.vertices = []
        self.create_buffer()
        print("Cleared vertices and buffer.")

    def add_vertex(self, x_fb, y_fb, line_color):
        new_vertex = (float(x_fb), float(y_fb))
        if 0 <= new_vertex[0] < self.fb_width and 0 <= new_vertex[1] < self.fb_height:
            last_vertex = self.vertices[-1] if self.vertices else None
            self.vertices.append(new_vertex)
            print(f"Added vertex (fb coords): ({new_vertex[0]:.2f}, {new_vertex[1]:.2f})")
            if last_vertex:
                filter(self.buffer, last_vertex[0], last_vertex[1],
                        new_vertex[0], new_vertex[1], line_color)
            self.draw_marker(new_vertex[0], new_vertex[1])
            self.needs_buffer_update = True
        else:
            print(f"Vertex ({new_vertex[0]:.2f}, {new_vertex[1]:.2f}) out of framebuffer bounds.")

    def draw_marker(self, x, y, size=2, color=MARKER_COLOR_RGB):
        x_c, y_c = int(round(x)), int(round(y))
        for i in range(max(0, x_c - size), min(self.fb_width, x_c + size + 1)):
            for j in range(max(0, y_c - size), min(self.fb_height, y_c + size + 1)):
                if 0 <= i < self.fb_width and 0 <= j < self.fb_height:
                    self.buffer[j, i] = color  # Y - строка, X - столбец

    def redraw_polygon_outline_aa(self, line_color):
        if len(self.vertices) < 2:
            return
        num_vertices = len(self.vertices)
        for i in range(num_vertices):
            p1 = self.vertices[i]
            p2 = self.vertices[(i + 1) % num_vertices]
            filter(self.buffer, p1[0], p1[1], p2[0], p2[1], line_color)
        self.needs_buffer_update = True

    def redraw_markers(self, marker_color):
        for vx, vy in self.vertices:
            self.draw_marker(vx, vy, color=marker_color)
        self.needs_buffer_update = True

class RasterizerApp:
    def __init__(self, win_width, win_height):
        if not glfw.init():
            sys.exit("Failed to initialize GLFW")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

        self.window = glfw.create_window(win_width, win_height,
                                         "Scanline Fill & Wu Line AA (Core Profile)",
                                         None, None)
        if not self.window:
            glfw.terminate()
            sys.exit("Failed to create GLFW window")

        glfw.make_context_current(self.window)
        glfw.swap_interval(1)

        fb_width, fb_height = glfw.get_framebuffer_size(self.window)

        self.app_state = AppState(fb_width, fb_height)
        self.shader_program = None
        self.texture_id = None
        self.quad_vao = None
        self.quad_vbo = None

        self._init_gl_resources()
        self._configure_gl_state()

        glfw.set_framebuffer_size_callback(self.window, self._resize_callback)
        glfw.set_key_callback(self.window, self._key_callback)
        glfw.set_mouse_button_callback(self.window, self._mouse_button_callback)


        self._update_texture()

    def _init_gl_resources(self):
        temp_vao = glGenVertexArrays(1)
        glBindVertexArray(temp_vao)

        try:
            vertex_shader = shaders.compileShader(VERTEX_SHADER_SRC, GL_VERTEX_SHADER)
            fragment_shader = shaders.compileShader(FRAGMENT_SHADER_SRC, GL_FRAGMENT_SHADER)
            self.shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
        except shaders.ShaderCompilationError as e:
            print("Shader compilation error:")
            print(e.args[0])
            print("Source:")
            print(e.args[1])
            glfw.terminate()
            sys.exit("Shader compilation failed")

        glBindVertexArray(0)
        glDeleteVertexArrays(1, [temp_vao])

        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)

        quad_vertices = np.array([
            -1.0, 1.0, 0.0, 1.0,
            -1.0, -1.0, 0.0, 0.0,
            1.0, 1.0, 1.0, 1.0,
            1.0, -1.0, 1.0, 0.0
        ], dtype=np.float32)

        self.quad_vao = glGenVertexArrays(1)
        self.quad_vbo = glGenBuffers(1)

        glBindVertexArray(self.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * ctypes.sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * ctypes.sizeof(GLfloat),
                              ctypes.c_void_p(2 * ctypes.sizeof(GLfloat)))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        print("OpenGL resources initialized (Shaders, Texture, VAO/VBO).")

    def _configure_gl_state(self):
        fb_width, fb_height = self.app_state.fb_width, self.app_state.fb_height
        glViewport(0, 0, fb_width, fb_height)
        glClearColor(*CLEAR_COLOR_FLOAT)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        print(f"OpenGL state configured. Viewport: {fb_width}x{fb_height}")

    def _update_texture(self):
        if self.app_state.buffer is None:
            return

        h, w, _ = self.app_state.buffer.shape
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        buffer_flipped = np.flipud(self.app_state.buffer)
        try:
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGB,
                            GL_UNSIGNED_BYTE, buffer_flipped.tobytes())
        except GLError:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB,
                         GL_UNSIGNED_BYTE, buffer_flipped.tobytes())
            print(f"Texture storage allocated/reallocated: {w}x{h}")

        glBindTexture(GL_TEXTURE_2D, 0)
        self.app_state.needs_buffer_update = False

    def run(self):
        while not glfw.window_should_close(self.window):
            glfw.poll_events()

            if self.app_state.needs_buffer_update:
                self._update_texture()

            self.render()
            glfw.swap_buffers(self.window)

            if not self.app_state.needs_buffer_update:
                glfw.wait_events_timeout(0.05)


        glDeleteVertexArrays(1, [self.quad_vao])
        glDeleteBuffers(1, [self.quad_vbo])
        glDeleteTextures(1, [self.texture_id])
        glDeleteProgram(self.shader_program)
        glfw.terminate()
        print("GLFW terminated, OpenGL resources released.")

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader_program)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)
        glBindTexture(GL_TEXTURE_2D, 0)
        glUseProgram(0)

    def _resize_callback(self, window, fb_width, fb_height):
        if fb_width > 0 and fb_height > 0:
            print(f"Framebuffer resized to: {fb_width}x{fb_height}")
            old_vertices = self.app_state.vertices
            self.app_state.fb_width = fb_width
            self.app_state.fb_height = fb_height
            self.app_state.create_buffer()
            self.app_state.vertices = old_vertices

            self.app_state.redraw_polygon_outline_aa(LINE_COLOR_RGB)
            self.app_state.redraw_markers(MARKER_COLOR_RGB)
            glViewport(0, 0, fb_width, fb_height)
            self._update_texture()

    def _key_callback(self, window, key, scancode, action, mods):
        if action == glfw.PRESS:
            if key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(window, True)
            elif key == glfw.KEY_C:
                print("Clearing...")
                self.app_state.clear_all()
            elif key == glfw.KEY_F:
                if len(self.app_state.vertices) >= 3:
                    print("Filling polygon...")
                    fill_polygon_scanline(self.app_state.buffer, self.app_state.vertices, FILL_COLOR_RGB)
                    self.app_state.redraw_polygon_outline_aa(LINE_COLOR_RGB)
                    self.app_state.redraw_markers(MARKER_COLOR_RGB)
                else:
                    print("Need at least 3 vertices to fill.")

    def _mouse_button_callback(self, window, button, action, mods):
        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            xpos, ypos = glfw.get_cursor_pos(window)
            win_width, win_height = glfw.get_window_size(window)
            fb_width, fb_height = glfw.get_framebuffer_size(window)
            scale_x = fb_width / win_width if win_width > 0 else 1
            scale_y = fb_height / win_height if win_height > 0 else 1
            fb_x = xpos * scale_x
            fb_y = ypos * scale_y
            self.app_state.add_vertex(fb_x, fb_y, LINE_COLOR_RGB)

if __name__ == "__main__":
    app = RasterizerApp(INITIAL_WIN_WIDTH, INITIAL_WIN_HEIGHT)
    app.run()
