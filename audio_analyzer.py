import os
import csv
import numpy as np
import librosa
from pydub import AudioSegment

class AudioAnalyzer:
    def __init__(self, threshold_db=-25, min_interval_sec=0.5):
        """
        初始化音频分析器
        
        参数:
            threshold_db (float): 检测峰值的阈值（分贝），默认为-25dB
            min_interval_sec (float): 两次检测之间的最小间隔（秒），默认为0.5秒
        """
        self.threshold_db = threshold_db
        self.min_interval_sec = min_interval_sec
        
    def extract_audio_from_video(self, video_path, output_audio_path=None):
        """
        从视频文件中提取音频
        
        参数:
            video_path (str): 视频文件路径
            output_audio_path (str, optional): 输出音频文件路径，如果为None则不保存音频文件
            
        返回:
            tuple: (音频数据, 采样率)
        """
        if not os.path.exists(video_path):
            print(f"错误: 视频文件 {video_path} 不存在!")
            return None, None
        
        temp_wav_path = os.path.splitext(video_path)[0] + "_temp.wav"
        
        try:
            # 使用pydub提取音频并保存为WAV格式
            video = AudioSegment.from_file(video_path)
            video.export(temp_wav_path, format="wav")
            
            # 使用librosa加载音频文件
            y, sr = librosa.load(temp_wav_path, sr=None)
            
            # 如果需要保存音频文件，使用pydub将其导出为MP3格式
            if output_audio_path:
                os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
                video.export(output_audio_path, format="mp3")
                print(f"音频已保存到: {output_audio_path}")
            
            # 删除临时WAV文件
            os.remove(temp_wav_path)
            return y, sr
            
        except Exception as e:
            print(f"提取音频时出错: {str(e)}")
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
            return None, None
    
    def detect_arrow_hits(self, audio_data, sample_rate):
        """
        检测音频中的箭射中靶的时刻
        
        参数:
            audio_data (numpy.ndarray): 音频数据
            sample_rate (int): 采样率
            
        返回:
            list: 检测到的时间点列表（秒）
        """
        if audio_data is None or sample_rate is None:
            return []
        
        # 计算音量（取振幅的平方）
        volume = audio_data**2
        
        # 将阈值从分贝转换为振幅平方
        threshold = 10**(self.threshold_db/10)
        
        # 检测声音突变的时间点
        peaks = []
        last_peak_time = -self.min_interval_sec  # 初始化为负值，确保第一个峰值可以被检测
        
        for i, v in enumerate(volume):
            # 将索引转换为时间（秒）
            current_time = i / sample_rate
            
            # 如果音量超过阈值，并且与上一个峰值的时间间隔足够大
            if v > threshold and (current_time - last_peak_time) >= self.min_interval_sec:
                peaks.append(current_time)
                last_peak_time = current_time
        
        return peaks
    
    def save_hits_to_csv(self, hits_times, output_csv_path):
        """
        将检测到的箭射中靶的时间点保存到CSV文件
        
        参数:
            hits_times (list): 检测到的时间点列表（秒）
            output_csv_path (str): 输出CSV文件路径
            
        返回:
            bool: 成功返回True，失败返回False
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
            
            with open(output_csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['序号', '时间点(秒)', '时间点(分:秒)'])
                
                for i, time_sec in enumerate(hits_times):
                    # 将秒转换为分:秒格式
                    minutes = int(time_sec // 60)
                    seconds = time_sec % 60
                    time_str = f"{minutes}:{seconds:.2f}"
                    
                    writer.writerow([i+1, f"{time_sec:.2f}", time_str])
            
            print(f"箭射中靶的时间点已保存到: {output_csv_path}")
            return True
            
        except Exception as e:
            print(f"保存CSV文件时出错: {str(e)}")
            return False
    
    def analyze_video_audio(self, video_path, output_csv_path, output_audio_path=None):
        """
        分析视频中的音频，检测箭射中靶的时间点，并保存结果
        
        参数:
            video_path (str): 视频文件路径
            output_csv_path (str): 输出CSV文件路径，如果不是绝对路径，将保存到res/output目录
            output_audio_path (str, optional): 输出音频文件路径，如果为None则不保存音频文件
            
        返回:
            list: 检测到的时间点列表（秒）
        """
        # 检查output_csv_path是否为绝对路径，如果不是，则将其保存到res/output目录
        if not os.path.isabs(output_csv_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(current_dir, 'res', 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成基于视频文件名的CSV文件名
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            csv_filename = f"hits_{video_name}.csv"
            
            output_csv_path = os.path.join(output_dir, csv_filename)
            print(f"CSV文件将保存到: {output_csv_path}")
        
        # 从视频中提取音频
        audio_data, sample_rate = self.extract_audio_from_video(video_path, output_audio_path)
        
        if audio_data is None or sample_rate is None:
            print("无法提取音频，分析失败!")
            return []
        
        # 检测箭射中靶的时间点
        hits_times = self.detect_arrow_hits(audio_data, sample_rate)
        
        if len(hits_times) == 0:
            print("未检测到箭射中靶的声音!")
        else:
            print(f"检测到 {len(hits_times)} 次箭射中靶的声音")
            for i, time_sec in enumerate(hits_times):
                minutes = int(time_sec // 60)
                seconds = time_sec % 60
                print(f"  第 {i+1} 箭: {minutes}:{seconds:.2f}")
        
        # 保存结果到CSV文件
        self.save_hits_to_csv(hits_times, output_csv_path)
        
        return hits_times

# 如果直接运行此脚本
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python audio_analyzer.py <视频路径> <输出CSV路径> [输出音频路径]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_csv_path = sys.argv[2]
    
    # 可选参数
    output_audio_path = None
    if len(sys.argv) > 3:
        output_audio_path = sys.argv[3]
    
    # 创建音频分析器并分析视频
    analyzer = AudioAnalyzer()
    hits_times = analyzer.analyze_video_audio(video_path, output_csv_path, output_audio_path)
    
    sys.exit(0 if len(hits_times) > 0 else 1)