import cv2
import time
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

def select_cameras_by_input():
    # 创建GUI窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 显示输入对话框
    camera_input = simpledialog.askstring("摄像头选择", "请输入要开启的摄像头编号(用逗号分隔，如: 1,2):")
    
    if not camera_input:
        return None
    
    # 解析输入
    try:
        camera_indices = [int(idx.strip()) for idx in camera_input.split(',')]
        if not camera_indices:
            messagebox.showerror("错误", "未输入有效的摄像头编号")
            return None
            
        # 检查输入的摄像头是否可用
        available_cameras = []
        for idx in camera_indices:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                available_cameras.append(idx)
                cap.release()
            else:
                messagebox.showwarning("警告", f"摄像头 {idx} 不可用")
        
        if not available_cameras:
            messagebox.showerror("错误", "所有指定的摄像头都不可用")
            return None
            
        return available_cameras
    except ValueError:
        messagebox.showerror("错误", "请输入有效的数字，用逗号分隔")
        return None

def capture_from_selected_cameras(camera_indices):
    # 创建保存文件的目录
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_videos")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"创建保存目录: {save_dir}")
    
    # 初始化摄像头
    caps = []
    for idx in camera_indices:
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            # 设置摄像头分辨率
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            caps.append((idx, cap))
        else:
            print(f"无法打开摄像头 {idx}")
    
    if not caps:
        print("没有可用的摄像头")
        return
    
    # 设置显示窗口大小
    display_width = 640
    display_height = 360
    
    # 视频录制变量
    recording = False
    video_writers = {}
    
    try:
        while True:
            frames = {}
            display_frames = {}
            
            # 从所有摄像头读取图像
            for idx, cap in caps:
                ret, frame = cap.read()
                if not ret:
                    print(f"无法从摄像头 {idx} 获取图像")
                    continue
                
                frames[idx] = frame
                
                # 如果正在录制，写入视频帧
                if recording and idx in video_writers:
                    video_writers[idx].write(frame)
                    # 在录制中的画面上显示红点
                    cv2.circle(frame, (30, 30), 15, (0, 0, 255), -1)
                
                # 调整图像大小用于显示
                display_frames[idx] = cv2.resize(frame, (display_width, display_height))
                
                # 显示摄像头图像
                cv2.imshow(f"Camera {idx}", display_frames[idx])
            
            # 按键控制
            key = cv2.waitKey(1) & 0xFF
            
            # 按下's'键保存图像
            if key == ord('s'):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                for idx, frame in frames.items():
                    img_path = os.path.join(save_dir, f"camera{idx}_{timestamp}.jpg")
                    cv2.imwrite(img_path, frame)
                    print(f"图像已保存: {img_path}")
            
            # 按下'r'键开始/停止录制视频
            elif key == ord('r'):
                if not recording:
                    # 开始录制
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    # 使用更兼容的编码器
                    fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # 改为MJPG编码
                    for idx, frame in frames.items():
                        h, w = frame.shape[:2]
                        video_path = os.path.join(save_dir, f"video{idx}_{timestamp}.avi")
                        video_writers[idx] = cv2.VideoWriter(video_path, fourcc, 20.0, (w, h))
                        
                        # 检查视频写入器是否成功创建
                        if not video_writers[idx].isOpened():
                            print(f"无法创建视频写入器，摄像头 {idx}")
                            del video_writers[idx]
                        else:
                            print(f"开始录制视频: {video_path}")
                    
                    if video_writers:
                        recording = True
                    else:
                        print("无法开始录制，请检查编码器设置")
                else:
                    # 停止录制
                    recording = False
                    for writer in video_writers.values():
                        writer.release()
                    video_writers.clear()
                    print("视频录制已停止")
            
            # 按下'q'键退出
            elif key == ord('q'):
                break
    
    finally:
        # 释放资源
        if recording:
            for writer in video_writers.values():
                writer.release()
        for _, cap in caps:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # 选择摄像头
    camera_indices = select_cameras_by_input()
    
    # 如果成功选择了摄像头，开始捕获
    if camera_indices:
        capture_from_selected_cameras(camera_indices)
    else:
        print("未选择摄像头或选择被取消")
