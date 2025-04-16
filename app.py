from flask import Flask, request, jsonify, render_template, send_from_directory, url_for, session
import os
import subprocess
import uuid
import shutil
import time
import cv2
import numpy as np
import json
import csv
from audio_analyzer import AudioAnalyzer  # 导入AudioAnalyzer类
from video_compressor import VideoCompressor  # 导入VideoCompressor类

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key_here'  # 用于session

# 配置上传文件夹和输出文件夹
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res', 'output')
SAVED_VIDEOS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saved_videos')
CACHE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
CSV_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv_results')
COMBINED_VIDEOS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'combined_videos')
COMPRESSED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compressed_videos')

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(SAVED_VIDEOS_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)
os.makedirs(CSV_FOLDER, exist_ok=True)
os.makedirs(COMBINED_VIDEOS_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

# 视频缓存，用于存储最近分析的视频
VIDEO_CACHE = {}

# 清理过期缓存的函数
def clean_expired_cache(max_age=3600):  # 默认1小时过期
    current_time = time.time()
    expired_keys = []
    
    for key, cache_data in VIDEO_CACHE.items():
        if current_time - cache_data['timestamp'] > max_age:
            expired_keys.append(key)
            # 删除缓存文件
            try:
                if os.path.exists(cache_data['original_path']):
                    os.remove(cache_data['original_path'])
                if os.path.exists(cache_data['output_path']):
                    os.remove(cache_data['output_path'])
                # 删除压缩文件（如果存在）
                if 'compressed_path' in cache_data and cache_data['compressed_path'] and os.path.exists(cache_data['compressed_path']):
                    os.remove(cache_data['compressed_path'])
            except Exception as e:
                print(f"清理缓存文件出错: {str(e)}")
    
    # 从缓存字典中移除过期项
    for key in expired_keys:
        del VIDEO_CACHE[key]

@app.route('/')
def index():
    """渲染主页"""
    # 清理过期缓存
    clean_expired_cache()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理视频上传并调用Driver.py进行分析"""
    if 'video' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 获取压缩参数
    target_fps = request.form.get('target_fps', type=int)
    if not target_fps or target_fps <= 0:
        target_fps = None  # 不压缩帧率
    
    # 生成唯一文件名以避免冲突
    original_filename = file.filename
    cache_id = str(uuid.uuid4())
    filename = cache_id + os.path.splitext(original_filename)[1]
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # 保存上传的文件
    file.save(filepath)
    
    # 同时保存一份到saved_videos文件夹
    saved_filename = f"original_{os.path.splitext(original_filename)[0]}_{uuid.uuid4().hex[:8]}{os.path.splitext(original_filename)[1]}"
    saved_filepath = os.path.join(SAVED_VIDEOS_FOLDER, saved_filename)
    shutil.copy2(filepath, saved_filepath)
    
    # 保存到缓存文件夹
    cache_original_path = os.path.join(CACHE_FOLDER, f"original_{cache_id}{os.path.splitext(original_filename)[1]}")
    shutil.copy2(filepath, cache_original_path)
    
    try:
        # 如果需要压缩视频
        compressed_path = None
        if target_fps is not None:
            compressed_filename = f"compressed_{cache_id}.mp4"
            compressed_path = os.path.join(COMPRESSED_FOLDER, compressed_filename)
            
            # 使用VideoCompressor进行压缩
            compression_success = VideoCompressor.compress_video_framerate(
                filepath, compressed_path, target_fps
            )
            
            # 如果压缩成功，使用压缩后的视频进行分析
            if compression_success:
                analysis_input_path = compressed_path
            else:
                analysis_input_path = filepath
                compressed_path = None
        else:
            analysis_input_path = filepath
        
        # 调用Driver.py进行分析
        output_filename = f"output_{os.path.splitext(filename)[0]}.mp4"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # 构建命令并执行
        cmd = ['python', 
               os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Driver_web.py'), 
               analysis_input_path, 
               output_path]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return jsonify({
                'error': '分析过程中出错',
                'details': stderr.decode('utf-8', errors='replace')
            }), 500
        
        # 将分析结果也保存到saved_videos文件夹
        saved_output_filename = f"analyzed_{os.path.splitext(original_filename)[0]}_{uuid.uuid4().hex[:8]}.mp4"
        saved_output_path = os.path.join(SAVED_VIDEOS_FOLDER, saved_output_filename)
        shutil.copy2(output_path, saved_output_path)
        
        # 保存到缓存文件夹
        cache_output_path = os.path.join(CACHE_FOLDER, f"analyzed_{cache_id}.mp4")
        shutil.copy2(output_path, cache_output_path)
        
        # 将视频信息存入缓存
        cache_data = {
            'original_filename': original_filename,
            'original_path': cache_original_path,
            'output_path': cache_output_path,
            'saved_original': saved_filename,
            'saved_output': saved_output_filename,
            'timestamp': time.time()
        }
        
        # 如果有压缩视频，添加到缓存
        if compressed_path:
            cache_data.update({
                'compressed_path': compressed_path,
                'target_fps': target_fps
            })
        
        VIDEO_CACHE[cache_id] = cache_data
        
        # 返回成功信息和输出文件路径
        response_data = {
            'success': True,
            'message': '分析完成',
            'cache_id': cache_id,
            'original_filename': original_filename,
            'output_filename': output_filename,
            'output_url': f'/output/{output_filename}',
            'saved_original': saved_filename,
            'saved_output': saved_output_filename,
            'download_original_url': f'/saved_videos/{saved_filename}',
            'download_output_url': f'/saved_videos/{saved_output_filename}',
            'cache_original_url': f'/cache/original_{cache_id}{os.path.splitext(original_filename)[1]}',
            'cache_output_url': f'/cache/analyzed_{cache_id}.mp4',
            'hits_info': '箭矢位置信息包含笛卡尔坐标和极坐标，可在前端显示',
            'comparison_url': url_for('compare_videos', cache_id=cache_id)  # 添加视频对比页面链接
        }
        
        # 如果有压缩视频，添加到响应
        if compressed_path:
            compressed_filename = os.path.basename(compressed_path)
            response_data.update({
                'compressed': True,
                'target_fps': target_fps,
                'compressed_url': f'/compressed_videos/{compressed_filename}'
            })
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': f'处理过程中出错: {str(e)}'}), 500
    
    finally:
        # 可选：清理上传的临时文件
        # os.remove(filepath)
        pass

@app.route('/cache/<filename>')
def serve_cache(filename):
    """提供缓存中的视频文件"""
    return send_from_directory(CACHE_FOLDER, filename)

@app.route('/output/<filename>')
def serve_output(filename):
    """提供分析结果的视频文件"""
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/view_video/<filename>')
def view_video(filename):
    """在网页上直接查看视频"""
    video_path = os.path.join(SAVED_VIDEOS_FOLDER, filename)
    if not os.path.exists(video_path):
        return render_template('error.html', message='视频文件不存在')
    
    video_url = url_for('serve_saved_video', filename=filename)
    return render_template('view_video.html', video_url=video_url, filename=filename)

@app.route('/saved_videos/<filename>')
def serve_saved_video(filename):
    """提供保存的视频文件"""
    return send_from_directory(SAVED_VIDEOS_FOLDER, filename)

@app.route('/saved_videos')
def list_saved_videos():
    """列出所有保存的视频"""
    original_videos = []
    analyzed_videos = []
    
    for filename in os.listdir(SAVED_VIDEOS_FOLDER):
        if filename.startswith('original_'):
            original_videos.append({
                'filename': filename,
                'url': url_for('serve_saved_video', filename=filename),
                'view_url': url_for('view_video', filename=filename)  # 添加直接查看的URL
            })
        elif filename.startswith('analyzed_'):
            analyzed_videos.append({
                'filename': filename,
                'url': url_for('serve_saved_video', filename=filename),
                'view_url': url_for('view_video', filename=filename)  # 添加直接查看的URL
            })
    
    return render_template('saved_videos.html', 
                          original_videos=original_videos, 
                          analyzed_videos=analyzed_videos)

@app.route('/analyze_audio', methods=['POST'])
def analyze_audio():
    """处理视频上传并分析音频，生成CSV文件"""
    if 'video' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 获取可选参数
    threshold_db = request.form.get('threshold_db', -25, type=float)
    min_interval_sec = request.form.get('min_interval_sec', 0.5, type=float)
    
    # 生成唯一文件名以避免冲突
    original_filename = file.filename
    cache_id = str(uuid.uuid4())
    filename = cache_id + os.path.splitext(original_filename)[1]
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # 保存上传的文件
    file.save(filepath)
    
    # 同时保存一份到saved_videos文件夹
    saved_filename = f"original_{os.path.splitext(original_filename)[0]}_{uuid.uuid4().hex[:8]}{os.path.splitext(original_filename)[1]}"
    saved_filepath = os.path.join(SAVED_VIDEOS_FOLDER, saved_filename)
    shutil.copy2(filepath, saved_filepath)
    
    try:
        # 创建CSV文件名
        csv_filename = f"hits_{os.path.splitext(original_filename)[0]}_{uuid.uuid4().hex[:8]}.csv"
        csv_path = os.path.join(CSV_FOLDER, csv_filename)
        
        # 创建音频分析器并分析视频
        analyzer = AudioAnalyzer(threshold_db=threshold_db, min_interval_sec=min_interval_sec)
        hits_times = analyzer.analyze_video_audio(filepath, csv_path)
        
        if len(hits_times) == 0:
            return jsonify({
                'success': False,
                'message': '未检测到箭射中靶的声音',
                'cache_id': cache_id,
                'original_filename': original_filename,
                'saved_original': saved_filename,
                'download_original_url': f'/saved_videos/{saved_filename}'
            })
        
        # 返回成功信息和CSV文件路径
        return jsonify({
            'success': True,
            'message': f'分析完成，检测到 {len(hits_times)} 次箭射中靶的声音',
            'cache_id': cache_id,
            'original_filename': original_filename,
            'saved_original': saved_filename,
            'download_original_url': f'/saved_videos/{saved_filename}',
            'csv_filename': csv_filename,
            'download_csv_url': f'/csv_results/{csv_filename}',
            'hits_count': len(hits_times),
            'hits_times': hits_times
        })
    
    except Exception as e:
        return jsonify({'error': f'处理过程中出错: {str(e)}'}), 500
    
    finally:
        # 可选：清理上传的临时文件
        # os.remove(filepath)
        pass

@app.route('/csv_results/<filename>')
def serve_csv(filename):
    """提供CSV结果文件"""
    return send_from_directory(CSV_FOLDER, filename)

@app.route('/compressed_videos/<filename>')
def serve_compressed_video(filename):
    """提供压缩后的视频文件"""
    return send_from_directory(COMPRESSED_FOLDER, filename)

@app.route('/generate_polar_csv/<cache_id>', methods=['POST'])
def generate_polar_csv(cache_id):
    """查找并提供包含极坐标信息的实际CSV文件"""
    if cache_id not in VIDEO_CACHE:
        return jsonify({'error': '未找到相关视频缓存'}), 404

    cache_data = VIDEO_CACHE[cache_id]
    output_path = cache_data.get('output_path') # 使用get以防万一

    if not output_path:
        return jsonify({'error': '缓存数据中缺少输出路径信息'}), 404

    try:
        # 确定 Driver_web.py 生成的CSV文件的预期基本名称
        # 假设 output_path 类似于 'output/analyzed_{cache_id}.mp4'
        output_basename = os.path.basename(output_path)
        csv_basename_expected = os.path.splitext(output_basename)[0] + '_hits.csv'
        expected_csv_path = os.path.join(CSV_FOLDER, csv_basename_expected)

        # 检查预期的CSV文件是否存在
        if os.path.exists(expected_csv_path):
            csv_filename = csv_basename_expected
            # 返回成功信息和正确的CSV文件路径
            return jsonify({
                'success': True,
                'message': '找到分析结果CSV文件',
                'csv_filename': csv_filename,
                'download_csv_url': f'/csv_results/{csv_filename}'
            })
        else:
            # 如果严格按名称找不到，可以尝试基于cache_id搜索（不太推荐，但作为备选）
            # for filename in os.listdir(CSV_FOLDER):
            #     if cache_id in filename and filename.endswith('_hits.csv'):
            #         # ... 找到文件 ...
            #         break
            # else: # 如果循环结束没有break
            #     return jsonify({'error': f'未能找到与 {cache_id} 关联的 *_hits.csv 文件'}), 404

            # 更清晰的做法是直接报错，如果预期文件不存在
            app.logger.error(f"Expected CSV file not found: {expected_csv_path}")
            return jsonify({'error': f'未能找到预期的分析结果CSV文件: {csv_basename_expected}'}), 404

    except Exception as e:
        app.logger.error(f"Error finding CSV for cache_id {cache_id}: {str(e)}")
        return jsonify({'error': f'查找CSV文件时出错: {str(e)}'}), 500

@app.route('/generate_hits_csv/<cache_id>', methods=['POST'])
def generate_hits_csv(cache_id):
    """生成包含命中点信息的CSV文件"""
    if cache_id not in VIDEO_CACHE:
        return jsonify({'error': '未找到相关视频缓存'}), 404
    
    cache_data = VIDEO_CACHE[cache_id]
    output_path = cache_data['output_path']
    
    try:
        # 创建CSV文件名
        original_filename = cache_data['original_filename']
        csv_filename = f"hits_{os.path.splitext(original_filename)[0]}_{uuid.uuid4().hex[:8]}.csv"
        csv_path = os.path.join(CSV_FOLDER, csv_filename)
        
        # 从分析后的视频中提取命中点信息
        # 简化版：创建一个示例CSV文件
        with open(csv_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['箭号', '时间(秒)', 'X坐标', 'Y坐标', '得分'])
            # 添加示例数据，实际应用中需要替换为真实数据
            csv_writer.writerow([1, 5.2, 100, 150, 9])
            csv_writer.writerow([2, 12.8, 200, 250, 8])
            csv_writer.writerow([3, 20.5, 300, 350, 10])
        
        # 返回成功信息和CSV文件路径
        return jsonify({
            'success': True,
            'message': '命中点CSV文件生成成功',
            'csv_filename': csv_filename,
            'download_csv_url': f'/csv_results/{csv_filename}'
        })
    
    except Exception as e:
        return jsonify({'error': f'处理过程中出错: {str(e)}'}), 500

@app.route('/compare_videos/<cache_id>')
def compare_videos(cache_id):
    """展示分析前后的视频对比"""
    if cache_id not in VIDEO_CACHE:
        return render_template('error.html', message='未找到相关视频缓存')
    
    cache_data = VIDEO_CACHE[cache_id]
    
    # 获取原始视频和分析后视频的URL
    original_video_url = url_for('serve_cache', filename=f"original_{cache_id}{os.path.splitext(cache_data['original_filename'])[1]}")
    analyzed_video_url = url_for('serve_cache', filename=f"analyzed_{cache_id}.mp4")
    
    # 检查是否有关联的CSV文件
    csv_url = None
    csv_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv_results')
    for filename in os.listdir(csv_folder):
        if filename.startswith(f"hits_{os.path.splitext(cache_data['original_filename'])[0]}"):
            csv_url = url_for('serve_csv', filename=filename)
            break
    
    return render_template('video_comparison.html', 
                          original_video_url=original_video_url,
                          analyzed_video_url=analyzed_video_url,
                          csv_url=csv_url)

@app.route('/audio_analysis')
def audio_analysis_page():
    """渲染音频分析页面"""
    return render_template('audio_analysis.html')

@app.route('/multi_video')
def multi_video_page():
    """渲染多视频上传页面"""
    return render_template('multi_video.html')

@app.route('/upload_multi_videos', methods=['POST'])
def upload_multi_videos():
    """处理多个视频的上传和合并"""
    if 'videos[]' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    video_files = request.files.getlist('videos[]')
    if len(video_files) != 4:
        return jsonify({'error': '请上传4个视频文件'}), 400
    
    # 生成唯一的会话ID
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    # 保存上传的视频文件
    video_paths = []
    for i, video in enumerate(video_files):
        if video.filename == '':
            continue
        
        filename = f"video_{i+1}_{uuid.uuid4()}.mp4"
        filepath = os.path.join(session_folder, filename)
        video.save(filepath)
        video_paths.append(filepath)
    
    if len(video_paths) != 4:
        return jsonify({'error': '无效的视频文件'}), 400
    
    try:
        # 合并视频
        output_filename = f"combined_{uuid.uuid4()}.mp4"
        output_path = os.path.join(COMBINED_VIDEOS_FOLDER, output_filename)
        
        # 读取所有视频
        caps = [cv2.VideoCapture(path) for path in video_paths]
        
        # 获取视频属性
        frame_sizes = [(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                       int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))) for cap in caps]
        fps_rates = [cap.get(cv2.CAP_PROP_FPS) for cap in caps]
        
        # 使用最小的FPS
        target_fps = min(fps_rates)
        
        # 计算目标尺寸（2x2网格）
        max_width = max(frame_sizes[0][0], frame_sizes[2][0]) + max(frame_sizes[1][0], frame_sizes[3][0])
        max_height = max(frame_sizes[0][1], frame_sizes[1][1]) + max(frame_sizes[2][1], frame_sizes[3][1])
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, target_fps, (max_width, max_height))
        
        while True:
            frames = []
            all_success = True
            
            # 读取每个视频的帧
            for cap in caps:
                ret, frame = cap.read()
                if not ret:
                    all_success = False
                    break
                frames.append(frame)
            
            if not all_success:
                break
            
            # 调整每个帧的大小
            target_width = max_width // 2
            target_height = max_height // 2
            resized_frames = [cv2.resize(frame, (target_width, target_height)) for frame in frames]
            
            # 创建2x2网格
            top_row = np.hstack((resized_frames[0], resized_frames[1]))
            bottom_row = np.hstack((resized_frames[2], resized_frames[3]))
            combined_frame = np.vstack((top_row, bottom_row))
            
            # 写入合并后的帧
            out.write(combined_frame)
        
        # 释放资源
        for cap in caps:
            cap.release()
        out.release()
        
        # 清理临时文件
        shutil.rmtree(session_folder)
        
        return jsonify({
            'success': True,
            'message': '视频合并完成',
            'combined_video_url': f'/combined_videos/{output_filename}',
            'download_url': f'/download_combined/{output_filename}'
        })
        
    except Exception as e:
        return jsonify({'error': f'处理视频时出错: {str(e)}'}), 500

@app.route('/combined_videos/<filename>')
def serve_combined_video(filename):
    """提供合并后的视频文件"""
    return send_from_directory(COMBINED_VIDEOS_FOLDER, filename)

@app.route('/download_combined/<filename>')
def download_combined_video(filename):
    """下载合并后的视频文件"""
    return send_from_directory(COMBINED_VIDEOS_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)