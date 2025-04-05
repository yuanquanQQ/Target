from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
import os
import subprocess
import uuid
import shutil

app = Flask(__name__, static_folder='static', template_folder='templates')

# 配置上传文件夹和输出文件夹
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res', 'output')
SAVED_VIDEOS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saved_videos')

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(SAVED_VIDEOS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理视频上传并调用Driver.py进行分析"""
    if 'video' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 生成唯一文件名以避免冲突
    original_filename = file.filename
    filename = str(uuid.uuid4()) + os.path.splitext(original_filename)[1]
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # 保存上传的文件
    file.save(filepath)
    
    # 同时保存一份到saved_videos文件夹
    saved_filename = f"original_{os.path.splitext(original_filename)[0]}_{uuid.uuid4().hex[:8]}{os.path.splitext(original_filename)[1]}"
    saved_filepath = os.path.join(SAVED_VIDEOS_FOLDER, saved_filename)
    shutil.copy2(filepath, saved_filepath)
    
    try:
        # 调用Driver.py进行分析
        output_filename = f"output_{os.path.splitext(filename)[0]}.mp4"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # 构建命令并执行
        cmd = ['python', 
               os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Driver_web.py'), 
               filepath, 
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
        
        # 返回成功信息和输出文件路径
        return jsonify({
            'success': True,
            'message': '分析完成',
            'original_filename': original_filename,
            'output_filename': output_filename,
            'output_url': f'/output/{output_filename}',
            'saved_original': saved_filename,
            'saved_output': saved_output_filename,
            'download_original_url': f'/saved_videos/{saved_filename}',
            'download_output_url': f'/saved_videos/{saved_output_filename}'
        })
    
    except Exception as e:
        return jsonify({'error': f'处理过程中出错: {str(e)}'}), 500
    
    finally:
        # 可选：清理上传的临时文件
        # os.remove(filepath)
        pass

@app.route('/output/<filename>')
def serve_output(filename):
    """提供分析结果的视频文件"""
    return send_from_directory(OUTPUT_FOLDER, filename)

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
                'url': url_for('serve_saved_video', filename=filename)
            })
        elif filename.startswith('analyzed_'):
            analyzed_videos.append({
                'filename': filename,
                'url': url_for('serve_saved_video', filename=filename)
            })
    
    return render_template('saved_videos.html', 
                          original_videos=original_videos, 
                          analyzed_videos=analyzed_videos)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)