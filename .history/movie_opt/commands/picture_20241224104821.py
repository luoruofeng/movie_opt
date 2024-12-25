import os
import subprocess
import cv2
import re

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


def video_segment(args):
    # 如果路径为空，则使用当前目录
    path = args.srt_path if args.srt_path else os.getcwd()
    
    video = args.video_path if hasattr(args, "video_path") else None

    if video is None:
        raise ValueError("Missing required parameters: 'video_path'")
    
    video_extend = os.path.splitext(video)[1][1:]

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return

    print(f"字幕文件夹路径: {path}")
    print(f"输入视频文件: {video}")
    print(f"视频扩展名: {video_extend}")

    # 用于存储字幕片段信息
    segment_json = []

    # 遍历文件夹中的所有 .srt 文件
    for file_name in sorted(os.listdir(path), key=lambda x: int(x.split('-')[-1].split('.')[0])):
        if file_name.endswith(".srt"):
            srt_path = os.path.join(path, file_name)
            filename_without_ext = os.path.splitext(file_name)[0]
            print(f"处理字幕文件: {file_name}")

            with open(srt_path, "r", encoding="utf-8") as srt_file:
                lines = srt_file.readlines()

            # 匹配字幕时间的正则表达式
            time_pattern = r"(\d{2}:\d{2}:\d{2},\d{3})"

            # 找到第一行字幕的开始时间和最后一行字幕的结束时间
            start_time = None
            end_time = None

            for line in lines:
                match = re.findall(time_pattern, line)
                if match:
                    if start_time is None:
                        start_time = match[0]
                    end_time = match[-1]

            if start_time and end_time:
                segment_info = {
                    "filename": filename_without_ext,
                    "start": start_time,
                    "end": end_time
                }
                segment_json.append(segment_info)
                print(f"找到字幕片段: {segment_info}")

    # 创建存储片段的文件夹
    output_dir = os.path.join(os.path.dirname(video), "视频片段")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建文件夹: {output_dir}")

    # 对 segment_json 中的每个片段处理视频
    for segment in segment_json:
        output_filename = os.path.join(output_dir, f"{segment['filename']}." + video_extend)
        print(f"准备处理视频片段: {output_filename}")

        if not os.path.exists(output_filename):
            start_seconds = convert_to_seconds(segment['start'])
            end_seconds = convert_to_seconds(segment['end'])

            print(f"输出片段文件: {output_filename}")

            # 使用 ffmpeg 截取视频片段（这种方案结尾的位置准确 但是开始位置会提前）
            # 例如： ffmpeg -ss 678.750 -to 735.090 -accurate_seek -i "C:\Users\luoruofeng\Desktop\test\test_subtitled.mkv" -c copy -avoid_negative_ts 1 "C:\Users\luoruofeng\Desktop\test\test_subtitled999.mkv"
            try:
                # command = [
                #     "ffmpeg",
                #     "-ss", f"{start_seconds:.3f}",
                #     "-to", f"{end_seconds:.3f}",
                #     "-accurate_seek", 
                #     "-i", video,
                #     "-c", "copy",
                #     "-avoid_negative_ts", "1",
                #     output_filename
                # ]

                # 例如： ffmpeg -accurate_seek -i "C:\Users\luoruofeng\Desktop\test\test_subtitled.mkv" -ss 1162.620 -to 1486.070 "C:\Users\luoruofeng\Desktop\test\Lion King 2 1998-en@cn-9.mkv"
                command = [
                    "ffmpeg",
                    "-accurate_seek",
                    "-i", video,
                    "-ss", f"{start_seconds:.3f}",
                    "-to", f"{end_seconds:.3f}",
                    output_filename
                ]
                
                print(f"执行命令: {' '.join(command)}")
                subprocess.run(command, check=True)
                print(f"成功截取片段: {output_filename}")
            except subprocess.CalledProcessError as e:
                print(f"截取片段失败: {output_filename}, 错误: {e}")


def convert_to_seconds(timestamp):
    """
    将时间戳 (hh:mm:ss,ms) 转换为以秒为单位的浮点数。
    """
    hours, minutes, seconds, milliseconds = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", timestamp).groups()
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) * 0.001
    return total_seconds



def split_video(args):
    srt_path = args.srt_path if args.srt_path else os.getcwd()
    video = args.video_path if hasattr(args, "video_path") else None

    if video is None:
        raise ValueError("Missing required parameters: 'video_path'")

    video_extend = os.path.splitext(video)[1][1:]

    if not os.path.exists(srt_path):
        print(f"路径不存在: {srt_path}")
        return

    print(f"字幕文件夹路径: {srt_path}")
    print(f"输入视频文件: {video}")
    print(f"视频扩展名: {video_extend}")

    splite_endtime_json = {}

    if srt_path.endswith(".srt"):
        print(f"处理字幕文件: {srt_path}")

        with open(srt_path, "r", encoding="utf-8") as srt_file:
            lines = srt_file.readlines()

        for i in range(0, len(lines)):
            if re.match(r"^\d+$", lines[i].strip()):
                time_match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", lines[i + 1].strip())
                if time_match:
                    _, end_time = time_match.groups()
                    content = lines[i + 2].strip()
                    splite_endtime_json[content] = end_time

        print(f"提取的字幕时间: {splite_endtime_json}")

        screenshots_dir = os.path.join(os.path.dirname(video), "每行截图-"+video)
        os.makedirs(screenshots_dir, exist_ok=True)

        video_clips_dir = os.path.join(os.path.dirname(video), "每行视频-"+video)
        os.makedirs(video_clips_dir, exist_ok=True)

        video_name, _ = os.path.splitext(os.path.basename(video))

        id_counter = 1

        for content, end_time in splite_endtime_json.items():
            screenshot_name = f"{video_name}-{id_counter}.jpg"
            screenshot_path = os.path.join(screenshots_dir, screenshot_name)

            end_seconds = convert_to_seconds(end_time)
            # ffmpeg -y -i "C:\Users\luoruofeng\Desktop\test\视频片段\Lion King 2 1998-en@cn-3.mkv" -ss 5 -vframes 1 -vf scale=320:-1 -q:v 2 "C:\Users\luoruofeng\Desktop\test\视频片段\每行截图\Lion King 2 1998-en@cn-3-1.jpg"
            command = [
                "ffmpeg", "-y", "-i", video, "-ss", str(end_seconds), "-vframes", "1","-q:v", "2", screenshot_path
            ]
            print(f"执行命令: {' '.join(command)}")
            subprocess.run(command)

            print(f"生成截图: {screenshot_path}")

            clip_name = f"{video_name}-{id_counter}.mp4"
            clip_path = os.path.join(video_clips_dir, clip_name)

            command = [
                "ffmpeg", "-y", "-loop", "1", "-i", screenshot_path, "-c:v", "libx264", "-t", "3", "-pix_fmt", "yuv420p", clip_path
            ]
            print(f"执行命令: {' '.join(command)}")
            subprocess.run(command)

            print(f"生成视频片段: {clip_path}")
            id_counter += 1