import cv2
import os

class VideoCompressor:
    """视频压缩工具类，用于压缩视频帧率和尺寸"""
    
    @staticmethod
    def compress_video_framerate(input_path, output_path, target_fps=30):
        """
        压缩视频帧率
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            target_fps: 目标帧率，默认30fps
        
        Returns:
            bool: 压缩是否成功
        """
        try:
            cap = cv2.VideoCapture(input_path)
            original_fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 如果目标帧率高于原始帧率，则使用原始帧率
            if target_fps > original_fps:
                target_fps = original_fps
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, target_fps, (width, height))
            
            # 计算帧采样间隔
            frame_interval = original_fps / target_fps
            
            frame_count = 0
            next_frame_to_keep = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 只保留需要的帧
                if frame_count >= next_frame_to_keep:
                    out.write(frame)
                    next_frame_to_keep += frame_interval
                
                frame_count += 1
            
            # 释放资源
            cap.release()
            out.release()
            
            return True
        except Exception as e:
            print(f"压缩视频帧率时出错: {str(e)}")
            return False
    
    @staticmethod
    def compress_video_resolution(input_path, output_path, target_width=None, target_height=None, scale_factor=None):
        """
        压缩视频分辨率
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            target_width: 目标宽度，如果为None则根据scale_factor计算
            target_height: 目标高度，如果为None则根据scale_factor计算
            scale_factor: 缩放因子，如果target_width和target_height都为None，则使用此值
        
        Returns:
            bool: 压缩是否成功
        """
        try:
            cap = cv2.VideoCapture(input_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 计算目标尺寸
            if target_width is None and target_height is None:
                if scale_factor is None:
                    scale_factor = 0.5  # 默认缩放为原来的一半
                
                target_width = int(width * scale_factor)
                target_height = int(height * scale_factor)
            elif target_width is None:
                # 按比例计算宽度
                target_width = int(width * (target_height / height))
            elif target_height is None:
                # 按比例计算高度
                target_height = int(height * (target_width / width))
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (target_width, target_height))
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 调整帧大小
                resized_frame = cv2.resize(frame, (target_width, target_height))
                out.write(resized_frame)
            
            # 释放资源
            cap.release()
            out.release()
            
            return True
        except Exception as e:
            print(f"压缩视频分辨率时出错: {str(e)}")
            return False
    
    @staticmethod
    def compress_video(input_path, output_path, target_fps=None, target_width=None, target_height=None, scale_factor=None):
        """
        综合压缩视频（帧率和分辨率）
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            target_fps: 目标帧率，如果为None则不压缩帧率
            target_width: 目标宽度，如果为None则根据scale_factor计算
            target_height: 目标高度，如果为None则根据scale_factor计算
            scale_factor: 缩放因子，如果target_width和target_height都为None，则使用此值
        
        Returns:
            bool: 压缩是否成功
        """
        try:
            # 创建临时文件路径
            temp_path = output_path + ".temp.mp4"
            
            # 如果需要压缩帧率
            if target_fps is not None:
                # 先压缩帧率
                if not VideoCompressor.compress_video_framerate(input_path, temp_path, target_fps):
                    return False
                
                # 如果需要压缩分辨率
                if target_width is not None or target_height is not None or scale_factor is not None:
                    # 再压缩分辨率
                    result = VideoCompressor.compress_video_resolution(temp_path, output_path, 
                                                                      target_width, target_height, scale_factor)
                    # 删除临时文件
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return result
                else:
                    # 只压缩帧率，将临时文件重命名为输出文件
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(temp_path, output_path)
                    return True
            
            # 如果只需要压缩分辨率
            elif target_width is not None or target_height is not None or scale_factor is not None:
                return VideoCompressor.compress_video_resolution(input_path, output_path, 
                                                               target_width, target_height, scale_factor)
            
            # 如果不需要任何压缩，直接复制文件
            else:
                import shutil
                shutil.copy2(input_path, output_path)
                return True
                
        except Exception as e:
            print(f"压缩视频时出错: {str(e)}")
            # 清理可能的临时文件
            temp_path = output_path + ".temp.mp4"
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False