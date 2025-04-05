from VideoAnalyzer import VideoAnalyzer
from Sketcher import Sketcher
import cv2
import sys
import os

# 检查是否提供了命令行参数作为视频路径
if len(sys.argv) > 1:
    video_name = sys.argv[1]
    print(f"使用命令行提供的视频路径: {video_name}")
else:
    # 默认视频路径
    video_name = r"E:\xuexi\shejian\Target-Score-Detector_debugged-main0\Target-Score-Detector_debugged-main0\res\arrow_shift.mp4"
    print(f"使用默认视频路径: {video_name}")

# input
model = cv2.imread(r"E:\xuexi\shejian\Target-Score-Detector_debugged-main0\res\target.jpg")
bullseye_point = (325,309)
inner_diameter_px = 50
inner_diameter_inch = 1.5
rings_amount = 6
display_in_cm = False

# 检查视频文件是否存在
if not os.path.exists(video_name):
    print(f"错误: 视频文件 {video_name} 不存在!")
    sys.exit(1)

# get a sample frame from the video
cap = cv2.VideoCapture(video_name)
ret, test_sample = cap.read()

if not ret:
    print(f"错误: 无法读取视频 {video_name}!")
    sys.exit(1)

# calculate the sizes of the frame and the input
model_h, model_w, _ = model.shape
frame_h, frame_w, _ = test_sample.shape
pixel_to_inch = inner_diameter_inch / inner_diameter_px
pixel_to_cm = pixel_to_inch * 2.54
measure_unit = pixel_to_cm if display_in_cm else pixel_to_inch
measure_unit_name = 'cm' if display_in_cm else '"'

# 创建输出目录
output_dir = r"E:\xuexi\shejian\Target-Score-Detector_debugged-main0\Target-Score-Detector_debugged-main0\res\output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 生成输出文件名
video_basename = os.path.basename(video_name)
output_filename = os.path.join(output_dir, f"output_{os.path.splitext(video_basename)[0]}.mp4")

# analyze
print(f"开始分析视频: {video_name}")
print(f"分析结果将保存到: {output_filename}")
sketcher = Sketcher(measure_unit, measure_unit_name)
video_analyzer = VideoAnalyzer(video_name, model, bullseye_point, rings_amount, inner_diameter_px)
video_analyzer.analyze(output_filename, sketcher)
print(f"分析完成! 结果已保存到: {output_filename}")