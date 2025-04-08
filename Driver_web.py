from VideoAnalyzer import VideoAnalyzer
from Sketcher import Sketcher
import cv2
import sys
import os

def analyze_video(video_path, output_path):
    """分析视频并保存结果"""
    # 输入参数
    model = cv2.imread(r"E:\xuexi\shejian\Target-Score-Detector_debugged-main0\Target-Score-Detector_debugged-main0\res\target.jpg")
    bullseye_point = (325, 309)
    inner_diameter_px = 50
    inner_diameter_inch = 1.5
    rings_amount = 6
    display_in_cm = False
    
    # 检查视频文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 视频文件 {video_path} 不存在!")
        return False
    
    # 获取视频的一帧样本
    cap = cv2.VideoCapture(video_path)
    ret, test_sample = cap.read()
    
    if not ret:
        print(f"错误: 无法读取视频 {video_path}!")
        return False
    
    # 计算帧和输入的大小
    model_h, model_w, _ = model.shape
    frame_h, frame_w, _ = test_sample.shape
    pixel_to_inch = inner_diameter_inch / inner_diameter_px
    pixel_to_cm = pixel_to_inch * 2.54
    measure_unit = pixel_to_cm if display_in_cm else pixel_to_inch
    measure_unit_name = 'cm' if display_in_cm else '"'
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 分析
    print(f"开始分析视频: {video_path}")
    print(f"分析结果将保存到: {output_path}")
    
    sketcher = Sketcher(measure_unit, measure_unit_name)
    video_analyzer = VideoAnalyzer(video_path, model, bullseye_point, rings_amount, inner_diameter_px)
    video_analyzer.analyze(output_path, sketcher)
    
    print(f"分析完成! 结果已保存到: {output_path}")
    return True

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) < 3:
        print("用法: python Driver_web.py <视频路径> <输出路径>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_path = sys.argv[2]
    
    success = analyze_video(video_path, output_path)
    sys.exit(0 if success else 1)