import os
import subprocess
import cv2

def get_video_resolution(video_path):
    """使用 OpenCV 获取视频的分辨率"""
    try:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"无法打开视频文件: {video_path}")
            return None, None

        # 获取宽度和高度
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 释放视频文件
        cap.release()
        return width, height

    except Exception as e:
        print(f"获取视频分辨率时出错: {e}")
        return None, None


def is_portrait_video(width, height, aspect_ratio=(9, 16)):
    """判断视频是否是竖屏，默认判断9:16竖屏"""
    return height * aspect_ratio[0] == width * aspect_ratio[1]

def crop_to_portrait(video_path, output_path, target_resolution=(720, 1280)):
    """裁剪视频为竖屏，居中裁剪"""
    width, height = get_video_resolution(video_path)
    
    if width is None or height is None:
        print(f"无法获取视频分辨率: {video_path}")
        return

    if is_portrait_video(width, height):
        print(f"{video_path} 已经是竖屏视频，无需裁剪")
        return

    # 计算裁剪区域（居中裁剪）
    crop_width = int(height * target_resolution[0] / target_resolution[1])
    crop_x = (width - crop_width) // 2

    # 使用ffmpeg裁剪视频
    command = [
        'ffmpeg', '-i', video_path,
        '-vf', f'crop={crop_width}:{height}:{crop_x}:0',
        '-c:a', 'copy', output_path
    ]
    subprocess.run(command)
    print(f"已裁剪并保存: {output_path}")

def cut_pc2phone(args):
    
    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return
    
    print(f"视频文件夹路径: {args.path}")

    # 遍历文件夹中的所有视频文件
    for root, dirs, files in os.walk(args.path):
        for file in files:
            if file.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                video_path = os.path.join(root, file)
                output_path = os.path.join(root, f"cropped_{file}")
                
                crop_to_portrait(video_path, output_path)


def scale_pc2phone(args):
    print(f"srt路径 {args.path}")


def add_text():
    pass