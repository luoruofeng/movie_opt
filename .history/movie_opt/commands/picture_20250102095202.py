import os
from pkg_resources import resource_filename
import subprocess
import sys
import cv2
import re
from movie_opt.utils import *

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
            try:
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
                    start_time, end_time = time_match.groups()
                    content = lines[i + 2].strip()#英文在中文前的情况，否则调转
                    chinese_content = lines[i + 3].strip()
                    splite_endtime_json[content] = {
                        "st":start_time,
                        "et":end_time,
                        "cn":chinese_content
                    }
                    # splite_endtime_json[content] = end_time

        print(f"提取的字幕时间和内容: {splite_endtime_json}")

        video_name = os.path.splitext(os.path.basename(video))[0]
        screenshots_dir = os.path.join(os.path.dirname(video), "每行截图-"+video_name)
        os.makedirs(screenshots_dir, exist_ok=True)

        video_clips_dir = os.path.join(os.path.dirname(video), "每行发音视频-"+video_name)
        os.makedirs(video_clips_dir, exist_ok=True)

        video_clips_dir2 = os.path.join(os.path.dirname(video), "每行发音视频2-"+video_name)
        os.makedirs(video_clips_dir2, exist_ok=True)

        video_child_dir = os.path.join(os.path.dirname(video), "每行儿童发音视频-"+video_name)
        os.makedirs(video_child_dir, exist_ok=True)

        video_empty_dir = os.path.join(os.path.dirname(video), "每行跟读视频-"+video_name)
        os.makedirs(video_empty_dir, exist_ok=True)

        video_cn_dir = os.path.join(os.path.dirname(video), "每行中文视频-"+video_name)
        os.makedirs(video_cn_dir, exist_ok=True)

        video_split_dir = os.path.join(os.path.dirname(video), "每行分段视频-"+video_name)
        os.makedirs(video_split_dir, exist_ok=True)

        video_split_complete_dir = os.path.join(os.path.dirname(video), "每行完整视频-"+video_name)
        os.makedirs(video_split_complete_dir, exist_ok=True)

        video_name, _ = os.path.splitext(os.path.basename(video))

        # 按照行字幕分段原视频
        id = 1
        for content, times in splite_endtime_json.items():
            start_time = times["st"]
            end_time = times["et"]

            split_name = f"{video_name}-{id}.mp4"
            output_path = os.path.join(video_split_dir, split_name)

            start_seconds = convert_to_seconds(start_time)
            end_seconds = convert_to_seconds(end_time)+0.1

            video_totle_second = get_mp4_duration_ffmpeg(video)
            if end_seconds > video_totle_second:
                end_seconds = video_totle_second

            command = [
                "ffmpeg",
                "-accurate_seek",
                "-i", video,
                "-ss", f"{start_seconds:.3f}",
                "-to", f"{end_seconds:.3f}",
                output_path
            ]

            print(f"按行分段保存 {output_path}")
            subprocess.run(command, check=True)

            id += 1
        

        
        # 按照行分段原视频(上一行字幕的结束到这一行字幕的开始)
        id = 1
        st = "00:00:00,000"
        # 将字典的键值对转换为列表
        items = list(splite_endtime_json.items())
        for i, (content, times) in enumerate(items):
            if i == len(items) - 1:
                # 这是最后一行
                end_time = None
            else:
                end_time = times["et"]
            

            split_name = f"{video_name}-{id}.mp4"
            output_path = os.path.join(video_split_complete_dir, split_name)

            start_seconds = convert_to_seconds(st)
            video_totle_second = get_mp4_duration_ffmpeg(video)

            if end_time is None:
                end_seconds = get_mp4_duration_ffmpeg(video)
            else:
                end_seconds = convert_to_seconds(end_time)
                if end_seconds > video_totle_second:
                    end_seconds = video_totle_second

            command = [
                "ffmpeg",
                "-accurate_seek",
                "-i", video,
                "-ss", f"{start_seconds:.3f}",
                "-to", f"{end_seconds:.3f}",
                output_path
            ]

            print(f"按行分段完整保存 {output_path}")
            subprocess.run(command, check=True)
            
            st = end_time
            id += 1


        # 创建各种视频
        id_counter = 0

        for content, attr in splite_endtime_json.items():
            id_counter += 1
            screenshot_name = f"{video_name}-{id_counter}.jpg"
            screenshot_path = os.path.join(screenshots_dir, screenshot_name)


            # 若改行字幕少于20个字符不生成跟读视频
            if len(content) < 65:
                continue


            #edge-tts生成中文mp3
            cn_voice = os.path.join(os.path.dirname(video),"cn_temp.mp3")
            voice_command = [
                sys.argv[0],  # This is the key change: use sys.argv[0]
                "voice",
                "edge_tts_voice",
                "--content=" + attr["cn"],
                "--save_path=" + cn_voice,
                "--language=zh-cn"
            ]

            print("Executing command:", " ".join(voice_command))
            result = subprocess.run(voice_command, capture_output=True, text=True, check=True)
            print("Stdout:", result.stdout)
            print("Stderr:", result.stderr)
            print(f"File saved to: {cn_voice}")


            #edge-tts生成儿童发音mp3
            child_voice = os.path.join(os.path.dirname(video),"child_temp.mp3")
            voice_command = [
                sys.argv[0],  # This is the key change: use sys.argv[0]
                "voice",
                "edge_tts_voice",
                "--content=" + content,
                "--save_path=" + child_voice,
                "--language=en-child"
            ]

            print("Executing command:", " ".join(voice_command))
            result = subprocess.run(voice_command, capture_output=True, text=True, check=True)
            print("Stdout:", result.stdout)
            print("Stderr:", result.stderr)
            print(f"File saved to: {child_voice}")


            

            #edge-tts生成英国英语女发音mp3
            content_voice = os.path.join(os.path.dirname(video),"temp.mp3")
            voice_command = [
                sys.argv[0],  # This is the key change: use sys.argv[0]
                "voice",
                "edge_tts_voice",
                "--content=" + content,
                "--save_path=" + content_voice,
                "--voice=en-GB-SoniaNeural"
            ]

            print("Executing command:", " ".join(voice_command))
            result = subprocess.run(voice_command, capture_output=True, text=True, check=True)
            print("Stdout:", result.stdout)
            print("Stderr:", result.stderr)
            print(f"File saved to: {content_voice}")



            # #youdao翻译生成mp3
            # content_voice = os.path.join(os.path.dirname(video),"temp.mp3")
            # voice_command = [
            #     sys.argv[0],  # This is the key change: use sys.argv[0]
            #     "voice",
            #     "youdao_voice",
            #     "--content=" + content,
            #     "--save_path=" + content_voice,
            #     "--type=1"
            # ]

            # print("Executing command:", " ".join(voice_command))
            # result = subprocess.run(voice_command, capture_output=True, text=True, check=True)
            # print("Stdout:", result.stdout)
            # print("Stderr:", result.stderr)
            # print(f"File saved to: {content_voice}")

            #edge-tts生成美国英语男发音mp3
            content_voice2 = os.path.join(os.path.dirname(video),"temp2.mp3")
            voice_command = [
                sys.argv[0],  # This is the key change: use sys.argv[0]
                "voice",
                "edge_tts_voice",
                "--content=" + content,
                "--save_path=" + content_voice2,
                "--voice=en-US-AndrewMultilingualNeural"
            ]

            print("Executing command:", " ".join(voice_command))
            result = subprocess.run(voice_command, capture_output=True, text=True, check=True)
            print("Stdout:", result.stdout)
            print("Stderr:", result.stderr)
            print(f"File saved to: {content_voice2}")

            # #youdao翻译生成mp3（美音）
            # content_voice2 = os.path.join(os.path.dirname(video),"temp2.mp3")
            # voice_command2 = [
            #     sys.argv[0],  # This is the key change: use sys.argv[0]
            #     "voice",
            #     "youdao_voice",
            #     "--content=" + content,
            #     "--save_path=" + content_voice2,
            #     "--type=2"
            # ]

            # print("Executing command:", " ".join(voice_command2))

            # # Use subprocess.run for cleaner handling of output and errors (Python 3.5+).
            # result2 = subprocess.run(voice_command2, capture_output=True, text=True, check=True)

            # # Print the output (stdout and stderr) for debugging or logging.
            # print("Stdout:", result2.stdout)
            # print("Stderr:", result2.stderr)
            # print(f"File saved to: {content_voice2}")

            #拼接音频“1s空白”和“中文内容”
            cn_voice_duration = 0
            if os.path.exists(cn_voice):
                e = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "empty1s.mp3")
                merge_mp3_files(e , cn_voice)
                cn_voice_duration = get_mp3_duration_tinytag(cn_voice)
                print(f"voice_duration: {cn_voice_duration}")
                if cn_voice_duration is None:
                    continue

                if cn_voice_duration <= 0:
                    continue
            else:
                continue

            #拼接音频“1s空白”和“儿童内容”
            child_voice_duration = 0
            if os.path.exists(child_voice):
                e = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "empty1s.mp3")
                merge_mp3_files(e , child_voice)
                child_voice_duration = get_mp3_duration_tinytag(child_voice)
                print(f"voice_duration: {child_voice_duration}")
                if child_voice_duration is None:
                    continue

                if child_voice_duration <= 0:
                    continue
            else:
                continue

            #拼接音频“慢速”和“内容”
            voice_duration = 0
            if os.path.exists(content_voice):
                ding = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "ding.mp3")
                merge_mp3_files(ding , content_voice)
                voice_duration = get_mp3_duration_tinytag(content_voice)
                print(f"voice_duration: {voice_duration}")
                if voice_duration is None:
                    continue

                if voice_duration <= 0:
                    continue
            else:
                continue

            #拼接音频“1s空白”和“内容”（美音）
            voice_duration2 = 0
            if os.path.exists(content_voice2):
                empty = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "empty1s.mp3")
                merge_mp3_files(empty , content_voice2)
                voice_duration2 = get_mp3_duration_tinytag(content_voice2)
                print(f"voice_duration: {voice_duration2}")
                if voice_duration2 is None:
                    continue
                if voice_duration2 <= 0:
                    continue
            else:
                continue


            #创建每行所需要的截图
            end_seconds = convert_to_seconds(attr["et"])
            # ffmpeg -y -i "C:\Users\luoruofeng\Desktop\test\视频片段\Lion King 2 1998-en@cn-3.mkv" -ss 5 -vframes 1 -vf scale=320:-1 -q:v 2 "C:\Users\luoruofeng\Desktop\test\视频片段\每行截图\Lion King 2 1998-en@cn-3-1.jpg"
            command = [
                "ffmpeg", "-y", "-i", video, "-ss", str(end_seconds-0.5), "-vframes", "1","-q:v", "2", screenshot_path
            ]
            print(f"执行命令: {' '.join(command)}")
            subprocess.run(command)

            print(f"生成截图: {screenshot_path}")


            #创建每行儿童发音视频
            child_name = f"{video_name}-{id_counter}.mp4"
            child_path = os.path.join(video_child_dir, child_name)

            command = [
                "ffmpeg", "-y", 
                "-loop", "1", "-i", screenshot_path,  # 输入图片
                "-i", child_voice,                  # 输入音频
                "-c:v", "libx264",                    # 视频编码器
                "-t",  str(child_voice_duration),        # 视频持续时间
                "-pix_fmt", "yuv420p",                # 像素格式，确保兼容性
                "-c:a", "aac",                        # 音频编码器
                "-shortest",                          # 保证输出长度与最短流（音频或视频）匹配
                child_path                             # 输出文件路径
            ]

            print(f"执行命令: {' '.join(command)}")
            subprocess.run(command)

            print(f"生成视频片段: {child_path}")


            #创建每行中文视频
            cn_name = f"{video_name}-{id_counter}.mp4"
            cn_path = os.path.join(video_cn_dir, cn_name)

            command = [
                "ffmpeg", "-y", 
                "-loop", "1", "-i", screenshot_path,  # 输入图片
                "-i", cn_voice,                  # 输入音频
                "-c:v", "libx264",                    # 视频编码器
                "-t",  str(cn_voice_duration),        # 视频持续时间
                "-pix_fmt", "yuv420p",                # 像素格式，确保兼容性
                "-c:a", "aac",                        # 音频编码器
                "-shortest",                          # 保证输出长度与最短流（音频或视频）匹配
                cn_path                             # 输出文件路径
            ]

            print(f"执行命令: {' '.join(command)}")
            subprocess.run(command)

            print(f"生成视频片段: {cn_path}")




            #创建每行发音视频
            clip_name = f"{video_name}-{id_counter}.mp4"
            clip_path = os.path.join(video_clips_dir, clip_name)

            command = [
                "ffmpeg", "-y", 
                "-loop", "1", "-i", screenshot_path,  # 输入图片
                "-i", content_voice,                  # 输入音频
                "-c:v", "libx264",                    # 视频编码器
                "-t",  str(voice_duration),        # 视频持续时间
                "-pix_fmt", "yuv420p",                # 像素格式，确保兼容性
                "-c:a", "aac",                        # 音频编码器
                "-shortest",                          # 保证输出长度与最短流（音频或视频）匹配
                clip_path                             # 输出文件路径
            ]

            print(f"执行命令: {' '.join(command)}")
            subprocess.run(command)

            print(f"生成视频片段: {clip_path}")


            #创建每行发音视频2
            clip_name = f"{video_name}-{id_counter}.mp4"
            clip_path2 = os.path.join(video_clips_dir2, clip_name)

            command = [
                "ffmpeg", "-y", 
                "-loop", "1", "-i", screenshot_path,  # 输入图片
                "-i", content_voice2,                  # 输入音频
                "-c:v", "libx264",                    # 视频编码器
                "-t",  str(voice_duration),        # 视频持续时间
                "-pix_fmt", "yuv420p",                # 像素格式，确保兼容性
                "-c:a", "aac",                        # 音频编码器
                "-shortest",                          # 保证输出长度与最短流（音频或视频）匹配
                clip_path2                             # 输出文件路径
            ]

            print(f"执行命令: {' '.join(command)}")
            subprocess.run(command)

            print(f"生成视频片段: {clip_path2}")
            
            

            #创建每行跟读视频
            command = [
                "ffmpeg", "-y", "-i", video, "-ss", str(end_seconds-0.5), "-vframes", "1","-q:v", "2", screenshot_path
            ]
            print(f"执行命令: {' '.join(command)}")
            subprocess.run(command)

            print(f"生成截图: {screenshot_path}")

            empty_name = f"{video_name}-{id_counter}.mp4"
            empty_path = os.path.join(video_empty_dir, empty_name)
            
            follow = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "follow.mp3")
            
            #计算跟读后的静音时长
            # 获取音频时长
            audio_duration = float(subprocess.check_output(
                ["ffprobe", "-i", follow, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"]
            ).strip())

            silence_duration = max(0, voice_duration - audio_duration)

            #填充静音并生成完整音频
            silent_audio = "silent.wav"
            combined_audio = "combined.wav"
            if silence_duration > 0:
                safe_remove(silent_audio, "删除音频")
                subprocess.run([
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",  # 生成静音
                    "-t", str(silence_duration), silent_audio
                ])
                safe_remove(combined_audio, "删除音频")
                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", follow, "-i", silent_audio, 
                    "-filter_complex", "[0:0][1:0]concat=n=2:v=0:a=1[out]", "-map", "[out]", combined_audio
                ])
                follow = combined_audio  # 更新音频路径



            command = [
                "ffmpeg", "-y", 
                "-loop", "1", "-i", screenshot_path,  # 输入图片
                "-i", follow,                  # 输入音频
                "-c:v", "libx264",                    # 视频编码器
                "-t",  str(voice_duration),        # 视频持续时间
                "-pix_fmt", "yuv420p",                # 像素格式，确保兼容性
                "-c:a", "aac",                        # 音频编码器
                empty_path                             # 输出文件路径
            ]

            print(f"执行命令: {' '.join(command)}")
            subprocess.run(command)

            print(f"生成视频片段: {clip_path}")

            #删除句子朗读
            safe_remove(content_voice, "生成视频片段")
            safe_remove(content_voice2, "删除音频")
            safe_remove(cn_voice, "删除音频")
            safe_remove(child_voice, "删除音频")
            safe_remove(child_voice, "删除音频")
            safe_remove(combined_audio, "删除音频")
            safe_remove(silent_audio, "删除音频")
            
            

# 删除文件前检查是否存在
def safe_remove(file_path, description):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"{description}: {file_path}")
    else:
        print(f"{description} 文件不存在，跳过删除: {file_path}")