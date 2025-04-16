import cv2
import numpy as np
import sys
import os
import csv
import re

def extract_polar_coordinates(video_path, csv_path):
    """
    从分析后的视频中提取极坐标信息并保存到CSV文件
    
    Args:
        video_path: 分析后的视频路径
        csv_path: 输出CSV文件路径
    """
    # 打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频: {video_path}")
        return False
    
    # 准备CSV文件
    with open(csv_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['箭号', '距离(r)', '角度(θ)', 'X坐标', 'Y坐标', '得分'])
        
        arrow_count = 0
        processed_frames = 0
        
        # 读取视频帧
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 每隔30帧处理一次，减少重复
            if processed_frames % 30 == 0:
                # 提取极坐标信息
                polar_coords = extract_polar_from_frame(frame)
                
                # 如果找到新的极坐标，添加到CSV
                for coord in polar_coords:
                    if coord not in [(row[1], row[2]) for row in csv_writer]:
                        arrow_count += 1
                        r, theta, x, y, score = coord
                        csv_writer.writerow([arrow_count, r, theta, x, y, score])
            
            processed_frames += 1
    
    cap.release()
    return True

def extract_polar_from_frame(frame):
    """
    从视频帧中提取极坐标信息
    
    Args:
        frame: 视频帧
    
    Returns:
        list: 极坐标列表 [(r, theta, x, y, score), ...]
    """
    # 这里需要根据实际情况调整
    # 方法1: 使用OCR识别视频中的文字信息
    # 方法2: 分析视频中的标记点
    # 方法3: 从视频帧中的特定区域提取信息
    
    # 简化版实现：假设极坐标信息显示在视频的右下角
    # 实际实现需要根据视频中极坐标的显示方式调整
    
    # 示例：从帧中提取右下角区域
    h, w = frame.shape[:2]
    roi = frame[int(h*0.85):h, int(w*0.5):w]
    
    # 将ROI转换为灰度图
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # 使用OCR或模式匹配提取数字
    # 这里使用简化的模式匹配方法
    # 实际应用中可能需要使用pytesseract等OCR库
    
    # 示例数据，实际应用中需要替换为真实提取的数据
    # 格式: [(r, theta, x, y, score), ...]
    polar_coords = []
    
    # 使用正则表达式从图像中提取数字
    # 这里仅作为示例，实际应用中需要更复杂的图像处理
    
    # 返回提取的极坐标
    return polar_coords

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python extract_polar_coords.py <视频路径> <CSV输出路径>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    csv_path = sys.argv[2]
    
    if not os.path.exists(video_path):
        print(f"视频文件不存在: {video_path}")
        sys.exit(1)
    
    success = extract_polar_coordinates(video_path, csv_path)
    if success:
        print(f"极坐标CSV文件已生成: {csv_path}")
        sys.exit(0)
    else:
        print("生成极坐标CSV文件失败")
        sys.exit(1)