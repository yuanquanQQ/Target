from VideoAnalyzer import VideoAnalyzer
from Sketcher import Sketcher
import HitsManager
import GroupingMetre
import cv2
import sys
import os
import json
import csv
import numpy as np
import shutil
import VisualAnalyzer
from Geometry2D import calc_polar_coordinates

def analyze_with_hits_data(video_path, output_path, target_center=None):
    """
    分析视频并记录箭的信息，包括笛卡尔坐标和极坐标
    
    参数:
        video_path: 输入视频路径
        output_path: 输出视频路径
        target_center: 靶心坐标，如果为None则使用图像中心
    """
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    if target_center is None:
        target_center = (width // 2, height // 2)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    analyzer = VisualAnalyzer()
    frame_count = 0
    hits_data = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # 每30帧处理一次
        if frame_count % 30 == 0:
            # 分析当前帧
            hits = analyzer.find_suspect_hits(frame)
            
            if hits is not None and len(hits) > 0:
                for hit in hits:
                    x, y = hit[0], hit[1]  # 获取箭的笛卡尔坐标
                    r, theta = calc_polar_coordinates((x, y), target_center)  # 计算极坐标
                    
                    hit_info = {
                        'frame': frame_count,
                        'cartesian': {'x': float(x), 'y': float(y)},
                        'polar': {'r': float(r), 'theta': float(theta)},
                        'timestamp': frame_count / fps
                    }
                    hits_data.append(hit_info)
                    
                    # 在视频上绘制信息
                    cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)
                    cv2.putText(frame, f'R: {r:.1f}, θ: {theta:.2f}rad', 
                              (int(x) + 10, int(y) + 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # 添加靶心标记
        cv2.circle(frame, target_center, 5, (255, 0, 0), -1)
        
        out.write(frame)
        frame_count += 1
    
    # 保存箭的数据到JSON文件
    json_output_path = output_path.rsplit('.', 1)[0] + '_hits.json'
    with open(json_output_path, 'w') as f:
        json.dump(hits_data, f, indent=4)
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    return hits_data

def analyze_video(video_path, output_path):
    """分析视频并保存结果"""
    try:
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 输入参数
        model_path = os.path.join(current_dir, 'res', 'target.jpg')
        if not os.path.exists(model_path):
            print(f"错误: 靶心图片不存在: {model_path}")
            return False
            
        model = cv2.imread(model_path)
        if model is None:
            print(f"错误: 无法读取靶心图片: {model_path}")
            return False
            
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
        cap.release()
        
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
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 分析
        print(f"开始分析视频: {video_path}")
        print(f"分析结果将保存到: {output_path}")
        
        # 初始化必要的对象
        sketcher = Sketcher(measure_unit, measure_unit_name)
        video_analyzer = VideoAnalyzer(video_path, model, bullseye_point, rings_amount, inner_diameter_px)
        
        # 创建一个列表来存储箭矢信息
        hits_data = []
        
        # 修改 VideoAnalyzer 的 analyze 方法，使其返回箭矢信息
        def analyze_with_hits_data(output_path, sketcher):
            try:
                # 设置输出配置
                frame_size = (video_analyzer.frame_w, video_analyzer.frame_h)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(output_path, fourcc, 24.0, frame_size)
                
                frame_count = 0
                
                while True:
                    ret, frame = video_analyzer.cap.read()
                    
                    if ret:
                        bullseye, scoreboard = video_analyzer._analyze_frame(frame)
                        
                        # 增加一致命中的声誉
                        # 或将它们添加为新候选
                        for hit in scoreboard:
                            # 从元组创建Hit对象
                            hit_point = hit[0]  # (x, y)坐标
                            hit_score = hit[1]  # 分数
                            hit_obj = HitsManager.Hit(hit_point[0], hit_point[1], hit_score, bullseye)
                            HitsManager.sort_hit(hit_obj, 30, 15)
                        
                        # 降低不一致命中的声誉
                        HitsManager.discharge_hits()
                        
                        # 根据稍微移动的靶心点稳定所有命中
                        if type(bullseye) != type(None):
                            HitsManager.shift_hits(bullseye)
                        
                        # 引用命中组
                        candidate_hits = HitsManager.get_hits(HitsManager.CANDIDATE)
                        verified_hits = HitsManager.get_hits(HitsManager.VERIFIED)
                        
                        # 提取分组数据
                        grouping_contour = GroupingMetre.create_group_polygon(frame, verified_hits)
                        has_group = type(grouping_contour) != type(None)
                        grouping_diameter = GroupingMetre.measure_grouping_diameter(grouping_contour) if has_group else 0
                        
                        # 在帧上写入元数据
                        sketcher.draw_data_block(frame)
                        verified_scores = [h.score for h in verified_hits]
                        arrows_amount = len(verified_scores)
                        sketcher.type_arrows_amount(frame, arrows_amount, (0x0,0x0,0xff))
                        sketcher.type_total_score(frame, sum(verified_scores), arrows_amount * 10, (0x0,189,62))
                        sketcher.type_grouping_diameter(frame, grouping_diameter, (0xff,133,14))
                        
                        # 标记命中和分组
                        sketcher.draw_grouping(frame, grouping_contour)
                        sketcher.mark_hits(frame, candidate_hits, foreground=(0x0,0x0,0xff),
                                           diam=2, withOutline=False, withScore=False)
                        
                        sketcher.mark_hits(frame, verified_hits, foreground=(0x0,0xff,0x0),
                                           diam=5, withOutline=True, withScore=True)
                        
                        # 每30帧保存一次箭矢信息
                        if frame_count % 30 == 0 and verified_hits:
                            for hit in verified_hits:
                                # 获取箭矢的笛卡尔坐标和极坐标
                                cartesian_coords = hit.point
                                polar_coords = hit.polar_coords if hasattr(hit, 'polar_coords') else None
                                
                                if polar_coords:
                                    hits_data.append({
                                        'frame': frame_count,
                                        'cartesian': {'x': cartesian_coords[0], 'y': cartesian_coords[1]},
                                        'polar': {'r': polar_coords[0], 'theta': polar_coords[1]},
                                        'score': hit.score
                                    })
                                else:
                                    # 如果没有极坐标，创建相对于靶心的极坐标
                                    bullseye_relation = hit.bullseye_relation
                                    dx = cartesian_coords[0] - bullseye_relation[0]
                                    dy = cartesian_coords[1] - bullseye_relation[1]
                                    r = (dx**2 + dy**2)**0.5
                                    theta = np.arctan2(dy, dx)
                                    hits_data.append({
                                        'frame': frame_count,
                                        'cartesian': {'x': cartesian_coords[0], 'y': cartesian_coords[1]},
                                        'polar': {'r': r, 'theta': theta},
                                        'score': hit.score
                                    })
                        
                        frame_count += 1
                        
                        # 显示
                        cv2.imshow('Analysis', frame)
                        
                        # 将帧写入输出文件
                        out.write(frame)
                        
                        if cv2.waitKey(1) & 0xff == 27:
                            break
                    else:
                        print('视频流结束。')
                        break
                        
                # 正确关闭窗口
                video_analyzer.cap.release()
                out.release()
                cv2.destroyAllWindows()
                cv2.waitKey(1)
                
                # 保存箭矢信息到JSON文件
                hits_json_path = os.path.splitext(output_path)[0] + '_hits.json'
                with open(hits_json_path, 'w') as f:
                    json.dump(hits_data, f, indent=4)
                
                print(f"箭矢信息已保存到: {hits_json_path}")
                
                # 保存箭矢信息到CSV文件
                hits_csv_path = os.path.splitext(output_path)[0] + '_hits.csv'
                with open(hits_csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # 写入CSV头部
                    writer.writerow(['Frame', 'X', 'Y', 'Radius', 'Theta', 'Score'])
                    # 写入箭矢数据
                    for hit in hits_data:
                        writer.writerow([
                            hit['frame'],
                            hit['cartesian']['x'],
                            hit['cartesian']['y'],
                            hit['polar']['r'],
                            hit['polar']['theta'],
                            hit['score']
                        ])
                
                print(f"箭矢信息已保存到CSV文件: {hits_csv_path}")
                
                # 将CSV文件也复制到csv_results目录以方便访问
                try:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    csv_results_dir = os.path.join(current_dir, 'csv_results')
                    if not os.path.exists(csv_results_dir):
                        os.makedirs(csv_results_dir)
                    
                    csv_results_path = os.path.join(csv_results_dir, os.path.basename(hits_csv_path))
                    shutil.copy2(hits_csv_path, csv_results_path)
                    print(f"箭矢信息已复制到: {csv_results_path}")
                except Exception as e:
                    print(f"复制CSV文件时出错: {str(e)}")
                
                return hits_data
                
            except Exception as e:
                print(f"分析过程中出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        
        # 使用修改后的分析方法
        hits_data = analyze_with_hits_data(output_path, sketcher)
        
        if hits_data is not None:
            print(f"分析完成! 结果已保存到: {output_path}")
            return True
        else:
            print("分析失败!")
            return False
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) < 3:
        print("用法: python Driver_web.py <视频路径> <输出路径>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_path = sys.argv[2]
    
    success = analyze_video(video_path, output_path)
    sys.exit(0 if success else 1)