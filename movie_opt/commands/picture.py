import argparse
import os
import random
import traceback
from pkg_resources import resource_filename
import subprocess
import sys
import re
from movie_opt.utils import *
from movie_opt.commands.subtitle import count_srt_statistics
import logging
import os
from PIL import Image, ImageDraw, ImageFont
from movie_opt.commands.ai import score_for_sentence,explain_words,get_english_difficulty_local_llm,get_most_hard_words, init_ai,HARD_WORD_SCORE_MAP

def add_titles_to_images(video_path, folder_path):
    font_path = os.path.join(os.path.dirname(__file__), 'static', "SourceHanSerif-Bold.otf")
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    main_title_font_size = 180
    subtitle_font_size = 110
    main_title_color = (255, 20, 147)  # 亮桃红色
    subtitle_color = (255, 255, 255)  # 亮紫色
    background_color = (0, 0, 0, 128)  # 黑色半透明
    padding = 20  # 背景与文字的间距

    main_title_font = ImageFont.truetype(font_path, main_title_font_size)
    subtitle_font = ImageFont.truetype(font_path, subtitle_font_size)

    main_title_text = "今日英语口粮"
    subtitle_text = f"来吃《{video_name}》"

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            try:
                image = Image.open(file_path).convert("RGBA")
                img_width, img_height = image.size

                overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)

                # 计算主标题边界框
                main_title_bbox = draw.textbbox((0, 0), main_title_text, font=main_title_font)
                main_title_width = main_title_bbox[2] - main_title_bbox[0]
                main_title_height = main_title_bbox[3] - main_title_bbox[1]

                # 计算副标题边界框
                subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
                subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]

                # 背景总宽高
                bg_width = max(main_title_width, subtitle_width) + padding * 2
                bg_height = main_title_height + subtitle_height + padding * 3

                # 背景位置
                bg_x0 = (img_width - bg_width) // 2
                bg_y0 = (img_height - bg_height) // 2
                bg_x1 = bg_x0 + bg_width
                bg_y1 = bg_y0 + bg_height

                # 绘制背景矩形
                draw.rectangle([bg_x0, bg_y0, bg_x1, bg_y1], fill=background_color)

                # 主标题位置
                main_title_x = (img_width - main_title_width) // 2
                main_title_y = bg_y0 + padding

                # 副标题位置
                subtitle_x = (img_width - subtitle_width) // 2
                subtitle_y = main_title_y + main_title_height + padding

                # 绘制主标题和副标题
                draw.text((main_title_x, main_title_y), main_title_text, font=main_title_font, fill=main_title_color)
                draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=subtitle_color)

                # 合并图片和叠加层
                combined = Image.alpha_composite(image, overlay)
                combined = combined.convert("RGB")
                combined.save(file_path)

                print(f"已处理图片: {file_path}")

            except Exception as e:
                print(f"处理图片 {file_path} 时出错: {e}")



def add_info_text_to_images(video_path, folder_path, srt_path):
    # 字体路径
    font_path = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "SourceHanSerif-Bold.otf")
    font_size = 99
    font_color = (57, 255, 20)  # 荧光亮绿色
    stroke_color = (0, 0, 0)    # 黑色描边

    # 加载字体
    font = ImageFont.truetype(str(font_path), font_size)

    video_duration = convert_seconds(get_mp4_duration_cv2(video_path))
    arg_parser = argparse.ArgumentParser()
    arg_parser.path = srt_path
    linecount,wordcount= count_srt_statistics(arg_parser)

    # 要添加的文字内容
    text_lines = [
        "时长  "+video_duration,
        f"单词量 {wordcount}个",
        f"对话  {linecount}行"
    ]

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # 检查是否为图片文件（扩展名检查）
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            try:
                # 打开图片
                image = Image.open(file_path)
                draw = ImageDraw.Draw(image)

                # 获取图片宽度和高度
                img_width, img_height = image.size

                # 起始位置（左下角）
                margin = 20
                x = margin
                y = img_height - margin

                # 绘制每行文字
                for line in reversed(text_lines):  # 从下往上绘制
                    # 计算文本尺寸
                    text_bbox = draw.textbbox((x, y), line, font=font)
                    text_height = text_bbox[3] - text_bbox[1]

                    # 上移一行的高度
                    y -= text_height

                    # 绘制文本
                    draw.text(
                        (x, y), 
                        line, 
                        font=font, 
                        fill=font_color, 
                        stroke_width=2, 
                        stroke_fill=stroke_color
                    )

                # 保存处理后的图片（覆盖原图片）
                image.save(file_path)
                print(f"已处理图片: {file_path}")

            except Exception as e:
                print(f"处理图片 {file_path} 时出错: {e}")

def get_video_w_h(video_path):
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
    width, height = get_video_w_h(video_path)
    
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


    logging.info("segment_json:\n%s\n", segment_json)

    # 对 segment_json 中的每个片段处理视频
    for segment in segment_json:
        output_filename = os.path.join(output_dir, f"{segment['filename']}." + video_extend)
        print(f"准备处理视频片段: {output_filename}")

        if not os.path.exists(output_filename):
            start_seconds = timestamp_convert_to_seconds(segment['start'])
            end_seconds = timestamp_convert_to_seconds(segment['end'])

            print(f"输出片段文件: {output_filename}")

            # 使用 ffmpeg 截取视频片段（这种方案结尾的位置准确 但是开始位置会提前）
            try:
                command = [
                    "ffmpeg",
                    "-accurate_seek",
                    "-i", video,
                    "-ss", f"{start_seconds:.3f}",
                    "-to", f"{end_seconds:.3f}",
                    "-map", "0",  # 保留所有轨道
                    "-map_metadata", "-1",  # 清除全局元信息
                    "-c:v", "libx264",  # 强制重新编码视频
                    "-c:a", "aac",  # 强制重新编码音频
                    "-movflags", "use_metadata_tags",  # 生成符合新元信息标准的文件
                    output_filename
                ]
                
                print(f"执行命令: {' '.join(command)}")
                subprocess.run(command, check=True)
                print(f"成功截取片段: {output_filename}")
            except subprocess.CalledProcessError as e:
                print(f"截取片段失败: {output_filename}, 错误: {e}")
    
    

def split_complete_video(split_endtime_json_list,video_name,video_extension,video_split_complete_dir,video):
    # 按照行分段原视频-完整视频(上一行字幕的结束到这一行字幕的开始)
        st = "00:00:00,000"
        # 将字典的键值对转换为列表
        id_counter = 0
        for info in split_endtime_json_list:
            id_counter += 1
            start_time = info["st"]
            end_time = info["et"]
            cn_content = info["cn"]
            en_content = info["en"]

            if id_counter == len(split_endtime_json_list):
                # 这是最后一行
                end_time = None
            else:
                end_time = info["et"]
            

            split_name = f"{video_name}-{id_counter}{video_extension}"
            output_path = os.path.join(video_split_complete_dir, split_name)

            start_seconds = timestamp_convert_to_seconds(st)
            video_totle_second = get_mp4_duration_ffmpeg(video)

            if end_time is None:
                end_seconds = get_mp4_duration_ffmpeg(video)
            else:
                end_seconds = timestamp_convert_to_seconds(end_time)
                if end_seconds > video_totle_second:
                    end_seconds = video_totle_second

            command = [
                "ffmpeg",
                "-accurate_seek",
                "-i", video,
                "-ss", f"{start_seconds:.3f}",
                "-to", f"{end_seconds:.3f}",
                "-map", "0",  # 保留所有轨道
                "-map_metadata", "-1",  # 清除全局元信息
                "-c:v", "libx264",  # 强制重新编码视频
                "-c:a", "aac",  # 强制重新编码音频
                "-movflags", "use_metadata_tags",  # 生成符合新元信息标准的文件
                output_path
            ]

            logging.info(f"按行完整保存 {output_path} video:{video} command:{' '.join(command)} en_content:{en_content} cn_content:{cn_content}")
            subprocess.run(command, check=True)
            
            st = subtract_one_millisecond(end_time)

def split_different_video(split_endtime_json_list,video_name,video_extension,video,explain_dir,screenshots_dir,video_child_dir,video_cn_dir,video_clips_dir,video_clips_dir2,video_empty_dir,filter_count,filter_score):
    # 创建各种视频
    id_counter = 0
    for info in split_endtime_json_list:
        id_counter += 1
        start_time = info["st"]
        end_time = info["et"]
        cn_content = info["cn"]
        en_content = info["en"]

        need_explain_words = None
        
        set_words = set(en_content.split(" "))
        set_word_count = ''.join(str(item) for item in set_words)

        # 若该行字幕少于filter_count个字符不生成跟读视频
        if set_word_count < filter_count:
            logging.info(f"英文字幕数少于{filter_count}个字符不生成跟读视频 {en_content} id:{id_counter}")
            continue
        
        # 最难的单词分数低于filter_score分不生成跟读视频
        try:
            sentence_score = score_for_sentence(en_content)
            if sentence_score > 3:
                most_hard_words = get_most_hard_words(cn_content,en_content)
                score = get_english_difficulty_local_llm(most_hard_words,en_content)
                if score < filter_score:
                    logging.info(f"最难的单词分数低于{filter_score}分不生成跟读视频 {en_content} id:{id_counter}")
                    continue
                need_explain_words = most_hard_words
            else:
                logging.info(f"句子难度的分数低于3分不生成跟读视频 {en_content} id:{id_counter}")
                continue
        except Exception as e:
            logging.error(f"本地模型单词评分发送异常",exc_info=True)
            traceback.print_exc()
            continue

        if need_explain_words is not None:
            explain= explain_words(need_explain_words)
            if explain != None:
                explain_name = f"{video_name}-{id_counter}.png"
                explain_path = os.path.join(explain_dir, explain_name)
                create_png_with_text(explain,explain_path,background_alpha=70)
            
        screenshot_name = f"{video_name}-{id_counter}.jpg"
        screenshot_path = os.path.join(screenshots_dir, screenshot_name)
        
        #edge-tts生成中文mp3
        cn_voice = os.path.join(os.path.dirname(video),"cn_temp.mp3")
        voice_command = [
            sys.argv[0],  # This is the key change: use sys.argv[0]
            "voice",
            "edge_tts_voice",
            "--content=" + info["cn"],
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
            "--content=" + en_content,
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
            "--content=" + en_content,
            "--save_path=" + content_voice,
            "--voice=en-GB-SoniaNeural"
        ]

        print("Executing command:", " ".join(voice_command))
        result = subprocess.run(voice_command, capture_output=True, text=True, check=True)
        print("Stdout:", result.stdout)
        print("Stderr:", result.stderr)
        print(f"File saved to: {content_voice}")


        #edge-tts生成美国英语男发音mp3
        content_voice2 = os.path.join(os.path.dirname(video),"temp2.mp3")
        voice_command = [
            sys.argv[0],  # This is the key change: use sys.argv[0]
            "voice",
            "edge_tts_voice",
            "--content=" + en_content,
            "--save_path=" + content_voice2,
            "--voice=en-US-AndrewMultilingualNeural"
        ]

        print("Executing command:", " ".join(voice_command))
        result = subprocess.run(voice_command, capture_output=True, text=True, check=True)
        print("Stdout:", result.stdout)
        print("Stderr:", result.stderr)
        print(f"File saved to: {content_voice2}")

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
            logging.error(f"创建音频失败 {cn_voice}")
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
            logging.error(f"创建音频失败 {child_voice}")
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
            logging.error(f"创建音频失败 {content_voice}")
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
            logging.error(f"创建音频失败 {content_voice2}")
            continue


        #创建每行所需要的截图
        end_seconds = timestamp_convert_to_seconds(info["et"])
        # ffmpeg -y -i "C:\Users\luoruofeng\Desktop\test\视频片段\Lion King 2 1998-en@cn-3.mkv" -ss 5 -vframes 1 -vf scale=320:-1 -q:v 2 "C:\Users\luoruofeng\Desktop\test\视频片段\每行截图\Lion King 2 1998-en@cn-3-1.jpg"
        command = [
            "ffmpeg", "-y", "-i", video, "-ss", str(end_seconds-0.4), "-vframes", "1","-q:v", "2", screenshot_path
        ]
        logging.info(f"创建每行截图 video:{video} screenshot_path:{screenshot_path} command:{' '.join(command)}")
        subprocess.run(command)

        print(f"生成截图: {screenshot_path}")


        #创建每行儿童发音视频
        child_name = f"{video_name}-{id_counter}{video_extension}"
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

        logging.info(f"创建儿童发音视频 child_path:{child_path} command:{' '.join(command)}")
        subprocess.run(command)

        print(f"生成视频片段: {child_path}")
        # #添加大字体 “宝宝慢速” 到视频
        # add_text_to_video(child_path,"宝宝慢速")
        # logging.info(f"创建行视频-宝宝慢速 {child_path} {' '.join(command)}")
        

        #创建每行中文视频
        cn_name = f"{video_name}-{id_counter}{video_extension}"
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

        logging.info(f"创建每行中文视频: cn_path:{cn_path} command:{' '.join(command)}")
        subprocess.run(command)
        print(f"生成视频片段: {cn_path}")
        #添加 “中文” 到视频
        add_text_to_video(cn_path,"中文")
        logging.info(f"创建行视频-中文 {cn_path} {' '.join(command)}")



        #创建每行发音视频
        clip_name = f"{video_name}-{id_counter}{video_extension}"
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

        logging.info(f"创建每行发音视频: clip_path:{clip_path} command:{' '.join(command)}")
        subprocess.run(command)
        print(f"生成视频片段: {clip_path}")
        #添加 “美音慢速” 到视频
        add_text_to_video(clip_path,"英音慢速")
        logging.info(f"创建行视频-英音慢速 {clip_path} {' '.join(command)}")


        #创建每行发音视频2
        clip_name = f"{video_name}-{id_counter}{video_extension}"
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

        print(f"执行命令 创建每行发音视频2: clip_path2:{clip_path2} command:{' '.join(command)}")
        subprocess.run(command)

        print(f"生成视频片段: {clip_path2}")
        #添加 “美音慢速” 到视频
        add_text_to_video(clip_path2,"美音慢速")
        logging.info(f"创建行视频-美音慢速 {clip_path2} {' '.join(command)}")
        
        

        #创建每行跟读视频
        empty_name = f"{video_name}-{id_counter}{video_extension}"
        empty_path = os.path.join(video_empty_dir, empty_name)
        
        follow = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "follow.mp3")
        
        #计算跟读后的静音时长
        # 获取音频时长
        audio_duration = float(subprocess.check_output(
            ["ffprobe", "-i", ding, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"]
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
                "-i", ding, "-i", silent_audio, 
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

        print(f"创建跟读视频: empty_path:{empty_path} command:{' '.join(command)}")
        subprocess.run(command)
        print(f"生成视频 {empty_path}")
        #添加 “跟读” 到视频
        add_text_to_video(empty_path,"跟读")
        logging.info(f"创建行视频-跟读 {empty_path} {' '.join(command)}")

        #删除句子朗读
        safe_remove(content_voice, "生成视频片段")
        safe_remove(content_voice2, "删除音频")
        safe_remove(cn_voice, "删除音频")
        safe_remove(child_voice, "删除音频")
        safe_remove(child_voice, "删除音频")
        safe_remove(combined_audio, "删除音频")
        safe_remove(silent_audio, "删除音频")
            
def split_fragment_video(split_endtime_json_list,video_name,video_extension,video_split_dir,video):
    id_counter = 0
    for info in split_endtime_json_list:
        id_counter += 1
        start_time = info["st"]
        end_time = info["et"]
        cn_content = info["cn"]
        en_content = info["en"]

        split_name = f"{video_name}-{id_counter}{video_extension}"
        output_path = os.path.join(video_split_dir, split_name)

        start_seconds = timestamp_convert_to_seconds(start_time)
        end_seconds = timestamp_convert_to_seconds(end_time)+0.1

        video_totle_second = get_mp4_duration_ffmpeg(video)
        if end_seconds > video_totle_second:
            end_seconds = video_totle_second

        command = [
            "ffmpeg",
            "-accurate_seek",
            "-i", video,
            "-ss", f"{start_seconds:.3f}",
            "-to", f"{end_seconds:.3f}",
            "-map", "0",  # 保留所有轨道
            "-map_metadata", "-1",  # 清除全局元信息
            "-c:v", "libx264",  # 强制重新编码视频
            "-c:a", "aac",  # 强制重新编码音频
            "-movflags", "use_metadata_tags",  # 生成符合新元信息标准的文件
            output_path
        ]

        logging.info(f"按行分段保存 {output_path} video:{video} command:{' '.join(command)} en_content:{en_content}")
        subprocess.run(command, check=True)

def srt2json_info(srt_path):
    split_endtime_json_list = []
    with open(srt_path, "r", encoding="utf-8") as srt_file:
        lines = srt_file.readlines()

    for i in range(0, len(lines)):
        if re.match(r"^\d+$", lines[i].strip()):
            time_match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", lines[i + 1].strip())
            if time_match:
                start_time, end_time = time_match.groups()
                if detect_language(lines[i + 2].strip()) == "Chinese" or detect_language(lines[i + 2].strip()) == "Mixed" :
                    chinese_content = lines[i + 2].strip()
                    content = lines[i + 3].strip()
                    info= {
                        "st":start_time,
                        "et":end_time,
                        "cn":chinese_content,
                        "en":content
                    }
                else:
                    content = lines[i + 2].strip()
                    chinese_content = lines[i + 3].strip()
                    info = {
                        "st":start_time,
                        "et":end_time,
                        "cn":chinese_content,
                        "en":content
                    }
                split_endtime_json_list.append(info)
    return split_endtime_json_list

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

    video_extension = get_file_extension(video)


    if srt_path.endswith(".srt"):
        print(f"处理字幕文件: {srt_path}")
        split_endtime_json_list = srt2json_info(srt_path)
        print(f"提取的字幕时间和内容: {split_endtime_json_list}")
        logging.info("srt_path:%s\nsplit_endtime_json_list:\n%s\n",srt_path, split_endtime_json_list)

        video_name = os.path.splitext(os.path.basename(video))[0]
        screenshots_dir = os.path.join(os.path.dirname(video), "每行截图-"+video_name)
        os.makedirs(screenshots_dir, exist_ok=True)
        logging.info(f"创建文件夹:{screenshots_dir}")

        explain_dir = os.path.join(os.path.dirname(video), "每行解释图-"+video_name)
        os.makedirs(explain_dir, exist_ok=True)
        logging.info(f"创建文件夹:{explain_dir}")
        

        video_clips_dir = os.path.join(os.path.dirname(video), "每行发音视频-"+video_name)
        os.makedirs(video_clips_dir, exist_ok=True)
        logging.info(f"创建文件夹:{video_clips_dir}")

        video_clips_dir2 = os.path.join(os.path.dirname(video), "每行发音视频2-"+video_name)
        os.makedirs(video_clips_dir2, exist_ok=True)
        logging.info(f"创建文件夹:{video_clips_dir2}")

        video_child_dir = os.path.join(os.path.dirname(video), "每行儿童发音视频-"+video_name)
        os.makedirs(video_child_dir, exist_ok=True)
        logging.info(f"创建文件夹:{video_child_dir}")

        video_empty_dir = os.path.join(os.path.dirname(video), "每行跟读视频-"+video_name)
        os.makedirs(video_empty_dir, exist_ok=True)
        logging.info(f"创建文件夹:{video_empty_dir}")

        video_cn_dir = os.path.join(os.path.dirname(video), "每行中文视频-"+video_name)
        os.makedirs(video_cn_dir, exist_ok=True)
        logging.info(f"创建文件夹:{video_cn_dir}")

        video_split_dir = os.path.join(os.path.dirname(video), "每行分段视频-"+video_name)
        os.makedirs(video_split_dir, exist_ok=True)
        logging.info(f"创建文件夹:{video_split_dir}")

        video_split_complete_dir = os.path.join(os.path.dirname(video), "每行完整视频-"+video_name)
        os.makedirs(video_split_complete_dir, exist_ok=True)
        logging.info(f"创建文件夹:{video_split_complete_dir}")

        video_name, _ = os.path.splitext(os.path.basename(video))

        init_ai() # 初始化ai

        # 按照行字幕-分段原视频
        split_fragment_video(split_endtime_json_list,video_name,video_extension,video_split_dir,video)

        # 按照行字幕-分段原视频-完整视频(上一行字幕的结束到这一行字幕的开始)
        split_complete_video(split_endtime_json_list,video_name,video_extension,video_split_complete_dir,video)

        # 按照行字幕-分段原视频-不同视频(上一行字幕的结束到这一行字幕的开始)
        split_different_video(split_endtime_json_list,video_name,video_extension,video,explain_dir,screenshots_dir,video_child_dir,video_cn_dir,video_clips_dir,video_clips_dir2,video_empty_dir,13,3)
        

# 删除文件前检查是否存在
def safe_remove(file_path, description):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"{description}: {file_path}")
    else:
        print(f"{description} 文件不存在，跳过删除: {file_path}")



def generate_images(args):
    video_file = args.path


    # 确保视频文件存在
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Video file not found. %s",video_file)

    # 获取视频时长
    video_duration = get_mp4_duration_ffmpeg(video_file)
    if video_duration is None:
        raise RuntimeError("无法获取视频时长，无法继续执行。")
    print(f"Video duration: {video_duration} seconds")

    # 定义保存文件夹路径
    base_dir = os.path.dirname(video_file)
    images_dir = os.path.join(base_dir, "images")
    pictures_dir = os.path.join(base_dir, "picture")

    # 创建文件夹
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(pictures_dir, exist_ok=True)

    # 随机截图 333 张
    print("Starting to generate 100 random screenshots...")
    for i in range(333):
        output_image = os.path.join(images_dir, f"frame_{i + 1}.png")
        print(f"创建333张封面 output_image:{output_image}")
        timestamp = random.uniform(0, video_duration)  # 随机时间戳
        if os.path.exists(output_image):
            os.remove(output_image)
        # 如果 -ss 位于 -i 参数之前，ffmpeg 会直接跳转到目标时间戳进行截图，速度会显著提高。
        ffmpeg_cmd = [
            "ffmpeg",
            "-ss", f"{timestamp}",
            "-i", video_file,
            "-frames:v", "1",
            output_image
        ]
        logging.info(f"创建333张封面 {' '.join(ffmpeg_cmd)}")
        subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        print(f"Generated screenshot: {output_image}")

    # 获取生成的图片路径
    saved_images = [os.path.join(images_dir, img) for img in os.listdir(images_dir) if img.endswith(".png")]
    print(f"Total screenshots saved: {len(saved_images)}")

    # 生成 444 张合成图片
    print("Starting to generate 444 combined images...")
    for i in range(444):
        # 随机选取 3 张图片
        selected_images = random.sample(saved_images, 3)
        image_objects = [Image.open(img) for img in selected_images]

        # 获取最大宽度和总高度
        widths, heights = zip(*(img.size for img in image_objects))
        max_width = max(widths)
        total_height = sum(heights)

        # 创建合成图片
        combined_image = Image.new("RGB", (max_width, total_height))

        # 逐张拼接
        y_offset = 0
        for img in image_objects:
            combined_image.paste(img, (0, y_offset))
            y_offset += img.height

        # 拉伸或压缩到 1080x1920
        combined_image_resized = combined_image.resize((1080, 1920), Image.Resampling.LANCZOS)

        # 保存为 JPG 格式
        output_image_path = os.path.join(pictures_dir, f"picture_{i + 1}.jpg")
        combined_image_resized.save(output_image_path, format="JPEG")
        print(f"Generated combined image: {output_image_path}")

    # 获取影片信息
    srts = find_srt_files(os.path.dirname(video_file))
    if srts is None or len(srts) < 1:
        logging.error(f"没有找到video同级的srt文件 video_file：{video_file}")
        return
    srt_path = srts[0]
    add_info_text_to_images(video_file,pictures_dir,srt_path)# 给图添加信息
    add_titles_to_images(video_file,pictures_dir)#给图片添加标题

    print(f"All images generated and saved to {pictures_dir}")