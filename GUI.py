from mttkinter import mtTkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
import os
import time
import threading
import NDI_get
from scipy.spatial.transform import Rotation as R
import yaml

# 视频尺寸
size_x = 1080
size_y = 800

# 显示图像尺寸
view_x = int(size_x * 0.4)
view_y = int(size_y * 0.4)

# 裁剪视频左上角和右下角坐标
x0 = 350
x1 = x0 + size_x
y0 = 120
y1 = y0 + size_y

fps = 20  # 保存视频的帧率
size = (size_x, size_y)  # 保存视频的大小

Tools_list = ['#8700339', '#8700340', '#8700449']
Tools_ID = {'#8700339': 0, '#8700340': 1, '#8700449': 2}

photo_path = 'photos'
video_path = 'videos'
NDI_path = 'NDI_information'


def video_init():
    cap = cv2.VideoCapture(1)
    cap.set(3, 1920)
    cap.set(4, 1080)
    # time.sleep(2)
    return cap


def Catch_photo(frame, path):
    cv2.imwrite(path, frame)


def save_NDI(tools, path):
    tools_dict = {}
    for tool in tools:
        if int(tool.get_status()) == 1:
            r = R.from_quat([tool.rot.q1, tool.rot.q2,
                            tool.rot.q3, tool.rot.q0])
            Rx, Ry, Rz = r.as_euler('xyz', degrees=True)
        else:
            Rx = 0.0
            Ry = 0.0
            Rz = 0.0
        tool_name = Tools_list[int(tool.get_parent_port_handle_id()) - 1]
        tools_dict[tool_name] = {'Q0': tool.rot.q0,
                                 'Qx': tool.rot.q1,
                                 'Qy': tool.rot.q2,
                                 'Qz': tool.rot.q3,
                                 'Rx': float(Rx),
                                 'Ry': float(Ry),
                                 'Rz': float(Rz),
                                 'Tx': tool.trans.x * 1000,
                                 'Ty': tool.trans.y * 1000,
                                 'Tz': tool.trans.z * 1000}
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(tools_dict, f, default_flow_style=False)


class creat_window():
    def __init__(self):
        self.is_catchvideo = False  # 是否截取视频

        self.num = 0
        self.video_num = 0
        self.photo_num = 0
        self.videoWriter = 0
        self.save_frame = 0

        if not os.path.exists(photo_path):
            os.makedirs(photo_path)
        if not os.path.exists(video_path):
            os.makedirs(video_path)
        if not os.path.exists(NDI_path + '/withphotos'):
            os.makedirs(NDI_path + '/withphotos')
        if not os.path.exists(NDI_path + '/withvideos'):
            os.makedirs(NDI_path + '/withvideos')

        # 主窗口设置
        self.root_window = tk.Tk()
        self.root_window.title('图像检测测试')
        self.root_window.geometry('%dx%d' % (view_x + 200, view_y + 85))
        self.root_window.resizable(width=False, height=False)

        # 超声图像
        image_frame = ttk.Frame(self.root_window, width=view_x, height=view_y)
        image_frame.place(x=10, y=20)
        self.image_photos = ttk.Label(image_frame)
        self.image_photos.place(x=0, y=0)

        # 开始录制按钮
        catch_start = tk.Button(
            self.root_window,
            text='开始录制',
            width=15,
            height=2,
            command=self.Catch_start)
        catch_start.place(x=10, y=view_y + 30)

        # 结束录制按钮
        catch_stop = tk.Button(
            self.root_window,
            text='结束录制',
            width=15,
            height=2,
            command=self.Catch_stop)
        catch_stop.place(x=150, y=view_y + 30)

        # 屏幕截屏按钮
        catch_photo = tk.Button(
            self.root_window,
            text='屏幕截屏',
            width=15,
            height=2,
            command=self.catch_photo)
        catch_photo.place(x=290, y=view_y + 30)

        # 窗口关闭
        self.root_window.protocol('WM_DELETE_WINDOW', self.close_window)

        # 命令反馈信息
        back_information = tk.LabelFrame(self.root_window, padx=10, pady=10)
        back_information.place(x=view_x + 20, y=view_y + 30, width=170)
        self.back_str = tk.StringVar()
        ttk.Label(
            back_information,
            textvariable=self.back_str).grid(
            column=0,
            row=0)

        # NDI信息显示
        NDI_information = tk.LabelFrame(
            self.root_window, text="NDI", padx=10, pady=10)
        NDI_information.place(x=view_x + 20, y=10, width=170)
        ttk.Label(NDI_information, text=" TOOL: ").grid(column=0, row=0)
        ttk.Label(NDI_information, text="四元数:").grid(column=0, row=1)
        ttk.Label(NDI_information, text="Q0:").grid(column=0, row=2)
        ttk.Label(NDI_information, text="Qx:").grid(column=0, row=3)
        ttk.Label(NDI_information, text="Qy:").grid(column=0, row=4)
        ttk.Label(NDI_information, text="Qz:").grid(column=0, row=5)
        ttk.Label(NDI_information, text="欧拉角:").grid(column=0, row=6)
        ttk.Label(NDI_information, text="Rx:").grid(column=0, row=7)
        ttk.Label(NDI_information, text="Ry:").grid(column=0, row=8)
        ttk.Label(NDI_information, text="Rz:").grid(column=0, row=9)
        ttk.Label(NDI_information, text="平移向量:").grid(column=0, row=10)
        ttk.Label(NDI_information, text="Tx:").grid(column=0, row=11)
        ttk.Label(NDI_information, text="Ty:").grid(column=0, row=12)
        ttk.Label(NDI_information, text="Tz:").grid(column=0, row=13)

        self.Tools = tk.StringVar()  # Tool字符串
        Tools_list = ttk.Combobox(
            NDI_information,
            width=10,
            textvariable=self.Tools,
            state='readonly')
        Tools_list['values'] = ('#8700339', '#8700340', '#8700449')
        Tools_list.current(0)  # 初始显示'8700339'
        Tools_list.grid(column=1, row=0)

        self.tool_q0 = tk.StringVar()
        self.tool_q1 = tk.StringVar()
        self.tool_q2 = tk.StringVar()
        self.tool_q3 = tk.StringVar()
        self.tool_rx = tk.StringVar()
        self.tool_ry = tk.StringVar()
        self.tool_rz = tk.StringVar()
        self.tool_tx = tk.StringVar()
        self.tool_ty = tk.StringVar()
        self.tool_tz = tk.StringVar()
        ttk.Label(
            NDI_information,
            textvariable=self.tool_q0).grid(
            column=1,
            row=2)
        ttk.Label(
            NDI_information,
            textvariable=self.tool_q1).grid(
            column=1,
            row=3)
        ttk.Label(
            NDI_information,
            textvariable=self.tool_q2).grid(
            column=1,
            row=4)
        ttk.Label(
            NDI_information,
            textvariable=self.tool_q3).grid(
            column=1,
            row=5)
        ttk.Label(
            NDI_information,
            textvariable=self.tool_rx).grid(
            column=1,
            row=7)
        ttk.Label(
            NDI_information,
            textvariable=self.tool_ry).grid(
            column=1,
            row=8)
        ttk.Label(
            NDI_information,
            textvariable=self.tool_rz).grid(
            column=1,
            row=9)
        ttk.Label(
            NDI_information,
            textvariable=self.tool_tx).grid(
            column=1,
            row=11)
        ttk.Label(
            NDI_information,
            textvariable=self.tool_ty).grid(
            column=1,
            row=12)
        ttk.Label(
            NDI_information,
            textvariable=self.tool_tz).grid(
            column=1,
            row=13)

        # 图像线程
        self.cap = video_init()
        photo_t = threading.Thread(target=self.video_show)
        photo_t.setDaemon(True)
        photo_t.daemon = True
        photo_t.start()

        # NDI线程
        self.NDI = NDI_get.PolarisDriverMine()
        NDI_t = threading.Thread(target=self.NDI_Get)
        NDI_t.setDaemon(True)
        NDI_t.daemon = True
        NDI_t.start()

        # 视频录制线程
        video_t = threading.Thread(target=self.video_catch)
        video_t.setDaemon(True)
        video_t.daemon = True
        video_t.start()

        self.root_window.mainloop()

    def close_window(self):
        self.cap.release()
        self.NDI.close()
        self.root_window.quit()

    def Catch_start(self):
        ndipath = NDI_path + '/withvideos/video%d' % self.video_num
        videopath = video_path + '/video%d' % self.video_num
        if not os.path.exists(ndipath):
            os.makedirs(ndipath)
        if not os.path.exists(videopath):
            os.makedirs(videopath)
        if not self.is_catchvideo:
            self.videoWriter = cv2.VideoWriter(
                'videos/video%d/video%d.avi' %
                (self.video_num, self.video_num), cv2.VideoWriter_fourcc(
                    *'XVID'), fps, size)
        self.is_catchvideo = True
        self.back_str.set('录制中···')

    def Catch_stop(self):
        if self.is_catchvideo:
            self.is_catchvideo = False
            self.videoWriter.release()
            self.video_num = self.video_num + 1
            self.num = 0
            self.back_str.set('视频已保存')

    def catch_photo(self):
        frame = self.save_frame
        tools = self.NDI.polaris_driver.get_tools()
        Catch_photo(frame, photo_path + '/photo%03d.jpg' % self.photo_num)
        save_NDI(tools, NDI_path + '/withphotos/NDI%03d.yaml' % self.photo_num)
        self.back_str.set('图像已保存')
        self.photo_num = self.photo_num + 1

    def video_show(self):
        while (self.cap.isOpened()):
            ret, frame = self.cap.read()
            if ret:
                # frame = cv2.flip(frame, 1)
                frame = frame[y0:y1, x0:x1]
                self.save_frame = frame

                # 将图像的通道顺序由BGR转换成RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                if isinstance(frame, np.ndarray):
                    frame = Image.fromarray(frame.astype(np.uint8))

                photo = ImageTk.PhotoImage(
                    image=frame.resize(
                        (view_x, view_y), Image.ANTIALIAS))
                self.image_photos.config(image=photo)

    def NDI_Get(self):
        while True:
            self.NDI.update_data()

            tool = self.NDI.polaris_driver.get_tools()[
                Tools_ID[self.Tools.get()]]
            if int(tool.get_status()) == 1:
                r = R.from_quat([tool.rot.q1, tool.rot.q2,
                                tool.rot.q3, tool.rot.q0])
                Rx, Ry, Rz = r.as_euler('xyz', degrees=True)
                self.tool_q0.set('%.4f' % tool.rot.q0)
                self.tool_q1.set('%.4f' % tool.rot.q1)
                self.tool_q2.set('%.4f' % tool.rot.q2)
                self.tool_q3.set('%.4f' % tool.rot.q3)
                self.tool_rx.set('%.2f' % Rx)
                self.tool_ry.set('%.2f' % Ry)
                self.tool_rz.set('%.2f' % Rz)
                self.tool_tx.set('%.2f' % (tool.trans.x * 1000))
                self.tool_ty.set('%.2f' % (tool.trans.y * 1000))
                self.tool_tz.set('%.2f' % (tool.trans.z * 1000))
                # time.sleep(0.1)
            else:
                self.tool_q0.set('')
                self.tool_q1.set('')
                self.tool_q2.set('')
                self.tool_q3.set('')
                self.tool_rx.set('')
                self.tool_ry.set('')
                self.tool_rz.set('')
                self.tool_tx.set('')
                self.tool_ty.set('')
                self.tool_tz.set('')

    def video_catch(self):
        timer = threading.Timer(1 / fps, self.video_catch)
        timer.start()
        if self.is_catchvideo:
            ndipath = NDI_path + '/withvideos/video%d' % self.video_num
            videopath = video_path + '/video%d' % self.video_num
            frame = self.save_frame
            tools = self.NDI.polaris_driver.get_tools()
            self.videoWriter.write(frame)
            Catch_photo(frame, videopath + '/photo%d.jpg' % self.num)
            save_NDI(tools, ndipath + '/NDI%d.yaml' % self.num)
            self.num = self.num + 1


if __name__ == '__main__':
    window = creat_window()
