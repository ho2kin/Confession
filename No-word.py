import random
from math import sin, cos, pi, log
from tkinter import *
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time

# CANVAS_WIDTH = 640
# CANVAS_HEIGHT = 480
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
CANVAS_CENTER_X = CANVAS_WIDTH / 2
CANVAS_CENTER_Y = CANVAS_HEIGHT / 2
IMAGE_ENLARGE = 11
HEART_COLOR = "#FF99CC"

class VideoPlayer:
    def __init__(self, video_path, canvas_width, canvas_height):
        self.video_path = video_path
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.cap = cv2.VideoCapture(video_path)
        self.current_frame = None
        self.photo = None
        self.is_playing = True
        
        # 获取视频信息
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame_index = 0
        
        # 启动视频播放线程
        self.video_thread = threading.Thread(target=self._video_loop, daemon=True)
        self.video_thread.start()
    
    def _video_loop(self):
        while self.is_playing:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # 调整视频尺寸以适应画布
                    frame = cv2.resize(frame, (self.canvas_width, self.canvas_height))
                    # 转换为RGB格式
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.current_frame = frame_rgb
                    self.current_frame_index += 1
                    
                    # 如果到达视频末尾，重新开始
                    if self.current_frame_index >= self.frame_count:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.current_frame_index = 0
                    
                    # 控制播放速度
                    time.sleep(1/self.fps)
                else:
                    # 视频读取失败，重新开始
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.current_frame_index = 0
            else:
                break
    
    def get_current_frame(self):
        if self.current_frame is not None:
            # 转换为PIL图像
            pil_image = Image.fromarray(self.current_frame)
            # 转换为PhotoImage
            self.photo = ImageTk.PhotoImage(pil_image)
            return self.photo
        return None
    
    def stop(self):
        self.is_playing = False
        if self.cap.isOpened():
            self.cap.release()


def heart_function(t, shrink_ratio: float = IMAGE_ENLARGE):
    x = 16 * (sin(t) ** 3)
    y = -(13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t))
    # 放大
    x *= shrink_ratio
    y *= shrink_ratio
    # 移到画布中央
    x += CANVAS_CENTER_X
    y += CANVAS_CENTER_Y
    return int(x), int(y)


def scatter_inside(x, y, beta=0.15):
    ratio_x = - beta * log(random.random())
    ratio_y = - beta * log(random.random())
    dx = ratio_x * (x - CANVAS_CENTER_X)
    dy = ratio_y * (y - CANVAS_CENTER_Y)
    return x - dx, y - dy


def shrink(x, y, ratio):
    force = -1 / (((x - CANVAS_CENTER_X) ** 2 +
                  (y - CANVAS_CENTER_Y) ** 2) ** 0.6)
    dx = ratio * force * (x - CANVAS_CENTER_X)
    dy = ratio * force * (y - CANVAS_CENTER_Y)
    return x - dx, y - dy


def curve(p):
    return 2 * (2 * sin(4 * p)) / (2 * pi)


class Heart:
    def __init__(self, generate_frame=20):
        self._points = set()  # 原始爱心坐标集合
        self._edge_diffusion_points = set()  # 边缘扩散效果点坐标集合
        self._center_diffusion_points = set()  # 中心扩散效果点坐标集合
        self.all_points = {}  # 每帧动态点坐标
        self.build(2000)
        self.random_halo = 1000
        self.generate_frame = generate_frame
        for frame in range(generate_frame):
            self.calc(frame)

    def build(self, number):
        for _ in range(number):
            t = random.uniform(0, 2 * pi)
            x, y = heart_function(t)
            self._points.add((x, y))
        # 爱心内扩散
        for _x, _y in list(self._points):
            for _ in range(3):
                x, y = scatter_inside(_x, _y, 0.05)
                self._edge_diffusion_points.add((x, y))
        # 爱心内再次扩散
        point_list = list(self._points)
        for _ in range(4000):
            x, y = random.choice(point_list)
            x, y = scatter_inside(x, y, 0.17)
            self._center_diffusion_points.add((x, y))

    @staticmethod
    def calc_position(x, y, ratio):
        force = 1 / (((x - CANVAS_CENTER_X) ** 2 +
                      (y - CANVAS_CENTER_Y) ** 2) ** 0.520)
        dx = ratio * force * (x - CANVAS_CENTER_X) + random.randint(-1, 1)
        dy = ratio * force * (y - CANVAS_CENTER_Y) + random.randint(-1, 1)
        return x - dx, y - dy

    def calc(self, generate_frame):
        ratio = 10 * curve(generate_frame / 10 * pi)
        halo_radius = int(4 + 6 * (1 + curve(generate_frame / 10 * pi)))
        halo_number = int(
            3000 + 4000 * abs(curve(generate_frame / 10 * pi) ** 2))
        all_points = []
        # 光环
        heart_halo_point = set()
        for _ in range(halo_number):
            t = random.uniform(0, 2 * pi)
            x, y = heart_function(t, shrink_ratio=11.6)
            x, y = shrink(x, y, halo_radius)
            if (x, y) not in heart_halo_point:
                heart_halo_point.add((x, y))
                x += random.randint(-14, 14)
                y += random.randint(-14, 14)
                size = random.choice((1, 2, 2))
                all_points.append((x, y, size))
        # 轮廓
        for x, y in self._points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 3)
            all_points.append((x, y, size))
        # 内容
        for x, y in self._edge_diffusion_points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 2)
            all_points.append((x, y, size))
        self.all_points[generate_frame] = all_points
        for x, y in self._center_diffusion_points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 2)
            all_points.append((x, y, size))
        self.all_points[generate_frame] = all_points
    

    def render(self, render_canvas, render_frame):
        for x, y, size in self.all_points[render_frame % self.generate_frame]:
            render_canvas.create_rectangle(
                x, y, x + size, y + size, width=0, fill=HEART_COLOR)

def draw(main: Tk, render_canvas: Canvas, render_heart: Heart, video_player: VideoPlayer, render_frame=0):
    render_canvas.delete('all')
    
    # 绘制视频背景
    video_frame = video_player.get_current_frame()
    if video_frame:
        render_canvas.create_image(0, 0, anchor=NW, image=video_frame)
    
    # 绘制爱心
    render_heart.render(render_canvas, render_frame)
    
    main.after(160, draw, main, render_canvas, render_heart, video_player, render_frame + 1)

if __name__ == '__main__':
    root = Tk()
    root.title("made by Hobin - 爱心动画 + 视频背景")
    
    # 创建画布
    canvas = Canvas(root, bg='black', height=CANVAS_HEIGHT, width=CANVAS_WIDTH)
    canvas.pack()
    
    # 创建视频播放器
    video_player = VideoPlayer("media/sea-fire.mp4", CANVAS_WIDTH, CANVAS_HEIGHT)
    
    # 创建爱心对象
    heart = Heart()
    
    # 启动动画
    draw(root, canvas, heart, video_player)
    
    # 程序关闭时停止视频播放
    def on_closing():
        video_player.stop()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()