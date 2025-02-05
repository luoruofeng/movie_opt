import json
import re
import shutil
from PIL import Image
import os
from tinytag import TinyTag
from pydub import AudioSegment
import subprocess
import shlex
from datetime import datetime, timedelta
import cv2
from pkg_resources import resource_filename
import logging
import chardet
import time
from functools import wraps
import re


def remove_non_alphanumeric(text: str) -> str:
    """
    只保留字符串中的大小写英文字母和数字，去除所有其他符号、空格和换行。

    :param text: 输入字符串
    :return: 处理后的字符串
    """
    return re.sub(r'[^a-zA-Z0-9]', '', text)
    

def remove_punctuation_and_spaces(text: str) -> str:
    """
    移除字符串中的所有标点符号和空格，并返回处理后的字符串。

    :param text: 需要处理的字符串
    :return: 去除标点符号和空格后的字符串
    """
    return re.sub(r'[，。！？、；：“”‘’()[\]{}<>《》,.\"\'?!<>*&$#@:;\s]', '', text)

def split_sentences(text: str):
    """
    根据标点符号将文本拆分为句子，并正确处理双引号包裹的句子。

    :param text: 输入的文本
    :return: 句子列表
    """
    # 正则匹配：识别句子，保留可能的双引号包裹情况
    pattern = re.compile(r'[^。！？]*?"[^"]*?"[^。！？]*?[。！？]|[^。！？]+[。！？]?')

    sentences = pattern.findall(text)

    # 去除前后空格
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences

def detect_language(text):
    """
    判断字符串是英文、中文，还是混合内容
    :param text: 输入字符串
    :return: "English", "Chinese", "Mixed"
    """
    english_pattern = re.compile(r'^[A-Za-z\s]+$')  # 仅包含英文字符和空格
    chinese_pattern = re.compile(r'^[\u4e00-\u9fff\s]+$')  # 仅包含中文字符和空格

    if english_pattern.match(text):
        return "English"
    elif chinese_pattern.match(text):
        return "Chinese"
    else:
        return "Mixed"



def remove_brackets_content(s,holder_token=""):
    return re.sub(r'\[[^\]]*\]|\([^)]*\)', holder_token, s)


def format_translation_srt(input_file: str):
    print("Formatting SRT file...")

    # 读取文件内容
    with open(input_file, "r", encoding="utf-8") as file:
        content = file.read()

    # 统一换行符格式，去除多余空行
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = re.sub(r'\n{2,}', '\n', content)

    # 匹配 SRT 字幕块
    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n([\s\S]+?)(?=\n\d+|\Z)', re.MULTILINE)
    
    subtitles = []
    content = remove_brackets_content(content)
    for match in pattern.finditer(content):
        number, timestamp, text_lines = match.groups()
        print(number, timestamp, text_lines)
        text_lines = text_lines.strip()

        # 去除多余空行
        line_content = text_lines.split("\n")
        if len(line_content) <= 1:
            print(f"删除字幕:只有中文或是只有中文的字幕 {number} {timestamp} {text_lines}")
            continue
        
        if line_content[0].isdigit():
            if int(number) == int(line_content[0]) - 1:
                print(f"删除没有内容只有时间的空行 {number} {timestamp} {text_lines}")
                continue

        # 只保留不为空的字幕块
        if text_lines:
            subtitles.append((number, timestamp, text_lines))

    # 格式化，保持原编号
    formatted_text = "\n\n".join(
        f"{number}\n{timestamp}\n{text}" for number, timestamp, text in subtitles
    )

    # 写回文件
    with open(input_file, "w", encoding="utf-8") as file:
        file.write(formatted_text)
        print(f"格式化完成 {input_file}")


def change_file_extension(file_path: str, new_extension: str) -> str:
    """
    将指定文件的扩展名修改为指定的新扩展名。

    :param file_path: 文件路径（可以是绝对路径或只有文件名）
    :param new_extension: 新的文件扩展名（不需要加"."）
    :return: 修改后新路径
    """
    directory, filename = os.path.split(file_path)  # 分离目录和文件名
    base_name, _ = os.path.splitext(filename)       # 获取无后缀的文件名
    new_filename = f"{base_name}.{new_extension}"   # 拼接新文件名
    new_path = os.path.join(directory, new_filename) if directory else new_filename  # 组合新路径
    return new_path


def convert_seconds(seconds):
    hours = int(seconds // 3600)  # 计算小时数
    minutes = int((seconds % 3600) // 60)  # 计算分钟数
    seconds = int(seconds % 60)  # 计算剩余秒数

    result = []

    # 如果小时数大于0，添加小时
    if hours > 0:
        result.append(f"{hours}小时")

    # 如果分钟数大于0，添加分钟
    if minutes > 0 or hours > 0:
        result.append(f"{minutes}分钟")

    # # 如果秒数大于0，添加秒
    # if seconds > 0:
    #     result.append(f"{seconds}秒")

    return "".join(result)



def rename_files_to_parent_folder(folder_path):
    """
    仅修改文件名与父文件夹不同的文件，否则跳过。
    
    :param folder_path: 文件夹的路径
    """
    if not os.path.isabs(folder_path):
        raise ValueError("Please provide an absolute folder path.")
    
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")
    
    # 获取父文件夹名称
    parent_folder_name = os.path.basename(folder_path)
    
    # 遍历文件夹中的所有文件
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        
        # 仅处理文件，跳过子文件夹
        if os.path.isfile(file_path):
            file_extension = os.path.splitext(file_name)[1]  # 保留原扩展名
            expected_file_name = f"{parent_folder_name}{file_extension}"
            
            # 仅当文件名与父文件夹名不同才重命名
            if file_name != expected_file_name and not str.startswith(file_name, "subtitle_"):
                new_file_path = os.path.join(folder_path, expected_file_name)
                os.rename(file_path, new_file_path)
                print(f"Renamed '{file_name}' to '{expected_file_name}'.")
            else:
                print(f"Skipped '{file_name}' (name matches parent folder).")


def rename_file_to_parent_folder(file_path):
    """
    将给定绝对路径的文件重命名为其父文件夹同名。
    
    :param file_path: 文件的绝对路径
    """
    if not os.path.isabs(file_path):
        raise ValueError("Please provide an absolute file path.")
    
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    
    # 获取父文件夹名和文件所在的目录路径
    parent_folder = os.path.basename(os.path.dirname(file_path))
    file_dir = os.path.dirname(file_path)
    
    # 构造新的文件路径
    new_file_path = os.path.join(file_dir, parent_folder + os.path.splitext(file_path)[1])
    
    # 重命名文件
    os.rename(file_path, new_file_path)
    print(f"Renamed '{file_path}' to '{new_file_path}'.")

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()  # 记录开始时间
        result = func(*args, **kwargs)  # 执行被装饰的函数
        end_time = time.time()  # 记录结束时间
        elapsed_time = end_time - start_time  # 计算总用时
        
        # 根据总用时选择显示分钟或小时
        if elapsed_time < 3600:  # 小于1小时，显示分钟
            print(f"Function '{func.__name__}' executed in {elapsed_time / 60:.2f} minutes")
        else:  # 超过或等于1小时，显示小时
            print(f"Function '{func.__name__}' executed in {elapsed_time / 3600:.2f} hours")
        
        return result  # 返回原函数的结果
    return wrapper


def convert_to_utf8(file_path):
    """
    将指定路径的文本文件转换为 UTF-8 编码并替换原文件。
    :param file_path: 文本文件路径
    """
    try:
        # 读取文件的原始二进制数据
        with open(file_path, 'rb') as file:
            raw_data = file.read()

        # 检测文件编码
        detected = chardet.detect(raw_data)
        original_encoding = detected['encoding']
        confidence = detected['confidence']

        print(f"检测到文件 '{file_path}' 的编码为: {original_encoding} (置信度: {confidence:.2f})")
        
        if original_encoding.lower() == 'utf-8':
            return 
        
        if not original_encoding:
            print(f"无法检测文件 '{file_path}' 的编码格式，跳过该文件。")
            return

        possible_encodings = ['utf-8', 'gbk', 'gb2312', 'big5', original_encoding]

        for encoding in possible_encodings:
            try:
                text_data = raw_data.decode(encoding)

                # **修正换行符**
                text_data = text_data.replace('\r\n', '\n').replace('\r', '\n')

                with open(file_path, 'w', encoding='utf-8', newline='\n') as file:
                    file.write(text_data)
                
                print(f"文件 '{file_path}' 已成功从 {encoding} 转换为 UTF-8 编码。")
                return
            except Exception as decode_error:
                print(f"尝试使用编码 {encoding} 处理文件时出错: {decode_error}")

        print(f"文件 '{file_path}' 无法被成功转换，跳过该文件。")
    except Exception as e:
        print(f"处理文件 '{file_path}' 时出错: {e}")



def check_file_numbers(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        # 提取编号
        numbers = []
        for line in lines:
            parts = line.strip().split("'")
            if len(parts) >= 2:
                file_name = parts[1]
                try:
                    number = int(file_name.split('_')[1].split('.')[0])
                    numbers.append(number)
                except ValueError:
                    print(f"警告: 无法解析编号的行: {line.strip()}")
        
        # 检查重复和缺失
        numbers.sort()
        min_num, max_num = numbers[0], numbers[-1]
        full_range = set(range(min_num, max_num + 1))
        missing = sorted(full_range - set(numbers))
        duplicates = sorted(set(num for num in numbers if numbers.count(num) > 1))

        # 输出结果
        if not missing and not duplicates:
            print(f"编号是连续的，没有缺失或重复。 file_path:{file_path}")
            logging.info(f"编号是连续的，没有缺失或重复。 file_path:{file_path}")
        else:
            if missing:
                print(f"缺失的编号: {missing}")
                logging.info("缺失的编号: {missing} file_path:{file_path}")
            if duplicates:
                print(f"重复的编号: {duplicates}")
                logging.info("缺失的编号: {duplicates} file_path:{file_path}")

        return missing, duplicates

    except FileNotFoundError:
        print(f"文件 {file_path} 不存在。")
        return [], []
    except Exception as e:
        print(f"发生错误: {e}")
        return [], []


def delete_txt_files(folder_path):
    """
    递归删除指定文件夹及其子文件夹中的所有 .txt 文件。

    :param folder_path: 要操作的文件夹路径
    """
    if not os.path.exists(folder_path):
        print(f"路径不存在: {folder_path}")
        return
    
    # 遍历文件夹中的所有文件和子文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 检查文件扩展名是否为 .txt
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"删除文件: {file_path}")
                except Exception as e:
                    print(f"无法删除文件 {file_path}: {e}")

def add_text_to_video(input_file, text):
    """
    在视频中添加文字，先保存到临时文件，再将临时文件替换原视频文件
    支持不同视频格式（如mp4, mkv等）

    :param input_file: 输入视频文件路径
    :param text: 要添加的文字
    """
    print(f"给视频添加字幕 {input_file} {text}")
    # 确保文件存在
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"输入文件 {input_file} 不存在")

    # 获取文件扩展名
    file_ext = os.path.splitext(input_file)[1].lower()

    # 临时文件路径
    temp_file = f"add_font_temp{file_ext}"

    # 如果临时文件已经存在，删除它
    if os.path.exists(temp_file):
        os.remove(temp_file)

    try:
        # 字体文件路径
        font_path = os.path.join(resource_filename(__name__,"commands"),'static', "SourceHanSerif-Bold.otf")  # 确保使用正确的路径
        # drawtext需要修改路径样式为 "C\:/Users/luoruofeng/Desktop/test3/SourceHanSerif-Bold.otf"
        font_path = font_path.replace("\\","/").replace(":","\\:")
        # 构造ffmpeg命令
        command = [
            "ffmpeg",
            "-i", input_file,  # 输入文件
            "-vf", (
                f"drawtext=text='{text}':"  # 动态设置文本
                f"fontfile='{font_path}':"  # 设置字体文件路径
                "fontcolor=white@0.5:"  # 设置字体颜色为白色，透明度50%
                "fontsize=222:"  # 设置字体大小
                "x=(w-text_w)/2:"  # 水平居中
                "y=(h-text_h)/2"  # 垂直居中
            ),
            "-codec:a", "copy",  # 保留原始音频
            temp_file  # 临时输出文件
        ]
        print(" ".join(command))
        # 使用 subprocess 执行命令
        subprocess.run(command, check=True)

        # 替换原文件为处理后的临时文件
        os.replace(temp_file, input_file)
        logging.info(f"视频添加文字 text:{text} input_file:{input_file} font_path:{font_path}")
    finally:
        # 操作完成后，删除临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)


def get_file_extension(file_path):
    """
    获取文件名或绝对路径文件的后缀。

    :param file_path: 文件名或文件的绝对路径。
    :return: 文件的后缀（包括 .），如果没有后缀则返回空字符串。
    """
    # 使用 os.path.splitext 分割路径和扩展名
    _, extension = os.path.splitext(file_path)
    return extension.lower()


def create_file_with_new_extension(file_path, new_extension):
    """
    在同一目录下创建一个新文件，该文件名称与原文件相同但扩展名不同，不覆盖原文件。

    :param file_path: 需要处理的文件的绝对路径。
    :param new_extension: 新的后缀（包含 . ，如 '.txt'）。
    :return: 新创建的文件路径。
    """
    if not os.path.isabs(file_path):
        raise ValueError("请提供文件的绝对路径")
    
    if not new_extension.startswith("."):
        raise ValueError("新后缀必须以 '.' 开头")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件 '{file_path}' 不存在")
    
    # 分离文件名和原始后缀
    file_base, _ = os.path.splitext(file_path)
    
    # 生成新文件路径
    new_file_path = f"{file_base}{new_extension}"
    
    # 复制原文件内容到新文件
    shutil.copy2(file_path, new_file_path)  # 保留原文件元数据（如修改时间）
    
    return new_file_path


def find_video_files(directory, extensions=None, recursive=False):
    """
    在给定目录下查找所有视频文件，并返回其绝对路径列表。
    
    :param directory: 要搜索的目录路径。
    :param extensions: 可选，视频文件的扩展名列表（默认支持常见视频格式）。
    :param recursive: 是否递归遍历子目录，默认为 False（仅遍历当前目录）。
    :return: 包含视频文件绝对路径的列表。
    """
    # 默认支持的扩展名
    if extensions is None:
        extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.mpeg']

    video_files = []

    if recursive:
        # 遍历目录及其子目录
        for root, _, files in os.walk(directory):
            for file in files:
                # 检查文件扩展名是否匹配
                if any(file.lower().endswith(ext) for ext in extensions):
                    video_files.append(os.path.abspath(os.path.join(root, file)))
    else:
        # 仅遍历当前目录
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in extensions):
                video_files.append(os.path.abspath(file_path))

    return video_files


def find_srt_files(directory, extensions=None, recursive=False):
    # 默认支持的扩展名
    if extensions is None:
        extensions = ['.srt']

    srt_files = []

    if recursive:
        # 遍历目录及其子目录
        for root, _, files in os.walk(directory):
            for file in files:
                # 检查文件扩展名是否匹配
                if any(file.lower().endswith(ext) for ext in extensions):
                    srt_files.append(os.path.abspath(os.path.join(root, file)))
    else:
        # 仅遍历当前目录
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in extensions):
                srt_files.append(os.path.abspath(file_path))

    return srt_files



def resize_video(video_path, target_width, target_height, file_extension=".mp4"):
    """
    使用 FFmpeg 将视频调整为指定的宽度和高度，直接覆盖原视频。

    :param video_path: str, 输入视频文件路径。
    :param target_width: int, 目标宽度。
    :param target_height: int, 目标高度。
    :raises ValueError: 如果 FFmpeg 命令失败。
    """
    width, height = get_video_w_h(video_path)
    print(f"视频分辨率: {width}x{height}")

    if (width, height) != (target_width, target_height):
        temp_path = f"{video_path}.temp"+file_extension
        command = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"scale={target_width}:{target_height}",
            "-c:a", "copy",
            temp_path
        ]
        print(" ".join(command))
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 如果视频调整成功，删除原视频并重命名临时文件
            if os.path.exists(video_path):
                os.remove(video_path)  # 删除原视频
            
            if os.path.exists(temp_path):
                os.rename(temp_path, video_path)  # 使用os.rename覆盖原视频
            print(f"视频分辨率已调整为: {target_width}x{target_height}，原视频已覆盖。")
        except subprocess.CalledProcessError as e:
            # 删除临时文件，避免残留
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise ValueError(f"FFmpeg 命令执行失败: {e.stderr.decode()}")
    else:
        print(f"视频分辨率相同无需修改: {width}x{height} video:{video_path}")



def get_video_w_h(video_path):
        """
        获取视频的宽高像素，例如 "1920x1080"。

        :param video_path: str, 视频文件的路径。
        :return: str, 视频的宽高像素，格式为 "宽x高"。
        :raises ValueError: 如果无法读取视频。
        """
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")

        # 获取视频的宽度和高度
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 释放视频对象
        cap.release()

        return width,height

def get_filename_without_extension(file_path):
    """
    获取绝对路径文件名，不包含后缀。

    :param file_path: str 文件的绝对路径
    :return: str 文件名（不带后缀）
    """
    # 获取文件名（带后缀）
    file_name_with_extension = os.path.basename(file_path)
    # 去掉后缀
    file_name_without_extension, _ = os.path.splitext(file_name_with_extension)
    return file_name_without_extension


def get_first_subfolder(folder_path):
    # 获取文件夹中的所有项，并过滤出文件夹（子文件夹）
    subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    
    # 如果有子文件夹，则返回第一个子文件夹的绝对路径
    if subfolders:
        first_subfolder = subfolders[0]
        return os.path.join(folder_path, first_subfolder)
    else:
        # 如果没有子文件夹，返回 None 或者你希望的提示
        return None

def subtract_one_millisecond(time_str: str) -> str:
    """
    减去1毫秒，并返回新的时间字符串，格式为 00:00:00,000。
    
    :param time_str: 输入时间字符串，格式为 00:00:00,000
    :return: 减去1毫秒后的时间字符串，格式为 00:00:00,000
    """
    if time_str is None:
        return None
    # 定义时间格式
    time_format = "%H:%M:%S,%f"
    try:
        # 将字符串解析为 datetime 对象
        time_obj = datetime.strptime(time_str, time_format)
        
        # 减去 1 毫秒
        updated_time_obj = time_obj - timedelta(milliseconds=1)
        
        # 格式化回字符串，并返回
        return updated_time_obj.strftime(time_format)[:-3]  # 去掉多余的微秒部分
    except ValueError:
        raise ValueError("时间格式错误，请使用 00:00:00,000 格式的时间字符串")



def timestamp_convert_to_seconds(timestamp):
    """
    将时间戳 (hh:mm:ss,ms) 转换为以秒为单位的浮点数。
    """
    hours, minutes, seconds, milliseconds = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", timestamp).groups()
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) * 0.001
    return total_seconds



# 统一音频编码和参数

def normalize_audio(video_files):
    """
    统一视频文件的音频编码和参数，并替换原文件。
    
    参数:
        video_files (list): 视频文件路径列表。
    """
    for video in video_files:
        # 使用原文件扩展名创建临时文件
        base_name, ext = os.path.splitext(video)
        temp_file = base_name + "_temp" + ext  # 保持与原始格式一致
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", video,             # 输入视频文件
                    "-c:v", "copy",          # 视频流直接复制
                    "-c:a", "aac",           # 音频重新编码为 AAC
                    "-b:a", "128k",          # 设置音频比特率
                    "-ar", "44100",          # 设置音频采样率
                    "-ac", "2",              # 设置音频声道数
                    temp_file                # 输出到临时文件
                ],
                check=True
            )
            # 替换原文件
            os.replace(temp_file, video)
            print(f"音频已统一: {video}")
        except subprocess.CalledProcessError as e:
            # 删除临时文件（如果存在）
            if os.path.exists(temp_file):
                os.remove(temp_file)
            print(f"处理失败: {video}, 错误: {e}")



def get_time_base(video_path):
    # 使用 shlex.quote 自动处理路径中的特殊字符（如空格），但不要加额外的引号
    safe_video_path = shlex.quote(video_path).strip("'")
    
    # 使用 ffprobe 获取视频的 time_base
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=time_base',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        safe_video_path  # 使用 shlex.quote 处理后的路径
    ]
    print(" ".join(command))  # 打印命令以供调试
    # 执行命令并捕获输出，显式指定 stderr 使用 utf-8 编码
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')

    # 检查 stderr 是否为空，并进行相应的处理
    if result.stderr:
        try:
            print(f"FFmpeg Error: {result.stderr.strip()}")
        except UnicodeDecodeError:
            print("Error decoding FFmpeg output.")
    
    # 获取 time_base 值
    time_base = result.stdout.strip()
    
    if time_base:
        return time_base
    else:
        print("Error: Could not retrieve time_base from the video.")
        return None



def change_timescale(video_path, timescale=1000,file_extension=".mp4"):
    # 判断当前视频的 timescale 是否已经是目标值
    temp_video_path = 'temp'+file_extension
    timebase = get_time_base(video_path)
    if timebase:
        print(f"Time base: {timebase}")
    # 如果当前 timescale 已经是目标值，则无需修改
    if timebase is not None and int(timebase.split("/")[-1]) == timescale:
        print(f"Timescale is already {timebase}, no changes made.")
        return
    
    
    # 使用 shlex.quote 自动处理路径中的特殊字符（如空格）
    safe_video_path = shlex.quote(video_path).strip("'")
    
    # 修改 timescale，并保存为 temp.mp4
    command = [
        'ffmpeg',
        '-i', video_path,
        '-c', 'copy',
        '-video_track_timescale', str(timescale),
        temp_video_path
    ]
    print(" ".join(command))
    try:
        subprocess.run(command, 
            stdin=subprocess.PIPE,  # 启用stdin管道
            stdout=subprocess.PIPE,  # 捕获标准输出
            stderr=subprocess.PIPE,  # 捕获标准错误
            text=True,  # 输出和输入以字符串形式处理
            encoding='utf-8'  # 显式指定 UTF-8 编码
        )
        
        # 删除原视频文件
        os.remove(video_path)
        
        # 将 temp.mp4 替换原视频文件
        os.rename(temp_video_path, video_path)
        print(f"Timescale updated to {timescale}, original video replaced.")
    except subprocess.CalledProcessError as e:
        # 删除临时文件（如果存在）
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        print(f"处理失败: {temp_video_path}, 错误: {e}")

# # 示例使用
# video_path = r"C:\Users\luoruofeng\Desktop\test\视频片段\每行中文视频-Lion King 2 1998-en@cn-3\Lion King 2 1998-en@cn-3-19.mp4"
# change_timescale(video_path,800)

def get_mp4_duration_ffmpeg(file_path):
    """
    使用 ffmpeg 获取 MP4 视频的总时长（秒），精确到小数点后 3 位。

    :param file_path: str, MP4 文件路径
    :return: float, 视频时长（秒）
    """
    try:
        # 确保路径为绝对路径
        file_path = os.path.abspath(file_path)

        # 调用 ffprobe 获取视频时长
        command = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=duration", "-of", "csv=p=0", file_path
        ]
        print(" ".join(command))
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"  # 显式指定编码
        )
        
        # 检查 ffprobe 是否成功执行
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe 执行失败: {result.stderr.strip()}")
        
        # 检查 stdout 是否为空
        if result.stdout is None or result.stdout.strip() == "":
            raise RuntimeError(f"ffprobe 输出为空: {result.stderr.strip()}")

        # 解析时长并保留 3 位小数
        duration = float(result.stdout.strip())
        return round(duration, 3)
    except Exception as e:
        print(f"发生错误: {e}")
        return None
    

def get_mp4_duration_cv2(file_path):
    """
    使用 OpenCV (cv2) 获取 MP4 视频的总时长（秒），精确到小数点后 3 位。

    :param file_path: str, MP4 文件路径
    :return: float, 视频时长（秒）
    """
    try:
        # 确保路径为绝对路径
        file_path = os.path.abspath(file_path)

        # 打开视频文件
        cap = cv2.VideoCapture(file_path)

        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频文件: {file_path}")

        # 获取视频的帧数和帧率
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # 视频的总帧数
        fps = cap.get(cv2.CAP_PROP_FPS)  # 视频的帧率

        # 计算视频时长（秒）
        duration = frame_count / fps

        # 释放视频捕获对象
        cap.release()

        # 保留 3 位小数
        return round(duration, 3)
    except Exception as e:
        print(f"发生错误: {e}")
        return None
    
def calculate_based_on_length(input_str: str) -> int:
    """
    根据字符串长度返回对应的值：
    - 如果长度是10的倍数，返回：长度 / 10 + 1。
    - 如果长度不是10的倍数，向下取到最近的10的倍数后再计算。

    Args:
        input_str (str): 输入字符串。

    Returns:
        int: 对应的返回值。
    """
    length = len(input_str)
    if length <= 10:
        return 2
    else:
        return (length // 10) + 2
    
    

def merge_mp3_files(mp3_path1, mp3_path2):
    """
    拼接两个 MP3 文件，并将结果保存到第二个路径。

    :param mp3_path1: 第一个 MP3 文件路径
    :param mp3_path2: 第二个 MP3 文件路径（保存路径）
    """
    try:
        # 加载 MP3 文件
        audio1 = AudioSegment.from_file(mp3_path1, format="mp3")
        audio2 = AudioSegment.from_file(mp3_path2, format="mp3")

        # 拼接音频
        combined_audio = audio1 + audio2

        # 将结果保存到第二个路径
        combined_audio.export(mp3_path2, format="mp3")
        print(f"拼接完成，结果保存到: {mp3_path2}")

    except Exception as e:
        print(f"处理音频时出错: {e}")

# 示例调用
# merge_mp3_files("path/to/first.mp3", "path/to/second.mp3")


# Example usage:
# concatenate_mp3("path_to_first.mp3", "path_to_second.mp3")

def get_mp3_duration_tinytag(file_path):
    """使用 tinytag 获取 MP3 文件时长（秒）"""
    try:
        audio = TinyTag.get(file_path)
        duration = audio.duration
        return duration
    except FileNotFoundError:
        return f"文件 '{file_path}' 未找到"
    except Exception as e:
        return f"发生错误：{e}"

def crop_image(image_path, width=None, height=None):
    # 打开图片
    with Image.open(image_path) as img:
        # 获取原始宽高
        original_width, original_height = img.size

        # 如果宽度为空，保持宽度不变
        if width is None:
            width = original_width

        # 计算裁剪区域
        left = 0
        top = 0
        right = width
        bottom = height if height is not None else original_height

        # 裁剪图片
        cropped_img = img.crop((left, top, right, bottom))

        # 覆盖原图片
        cropped_img.save(image_path)


def find_keywords_indices(line: str, key_words: list[str]) -> list[tuple[int, str]]:
    """
    在给定的行中找到包含关键词的位置及关键词本身。
    
    :param line: 需要搜索的字符串
    :param key_words: 关键词列表
    :return: 包含下标和关键词的列表
    """
    results = []
    for keyword in key_words:
        start = 0
        while (index := line.find(keyword, start)) != -1:  # 使用 `str.find` 找到关键词的位置
            results.append((index, keyword))
            start = index + 1  # 更新开始位置，避免重复查找
    return results

def assign_colors(lists, color_palette=None):
    """
    给多个列表赋予不同颜色，每个列表对应一个颜色。

    Args:
        lists: 一个二维列表，其中每个子列表对应一个需要赋色的元素组。
        color_palette: 可选，一个包含颜色名称的列表，用于自定义颜色。

    Returns:
        一个字典，键为元素，值为对应的颜色。
    """
    # 示例用法
    # lists = [["a","b"],["egg","dog"],["right","good"]]
    # result = assign_colors(lists)
    # print(result)

    if not color_palette:
        # 默认颜色列表，包含20种颜色
        color_palette = [
            'red', 'orange', 'yellow', 'green', 'blue', 'purple',
            'pink', 'brown', 'gray', 'cyan',
            'magenta', 'olive', 'maroon', 'navy', 'teal',
            'lime', 'aqua', 'fuchsia', 'silver', 'gold'
        ]

    color_dict = {}
    color_index = 0
    for sublist in lists:
        for item in sublist:
            color_dict[item] = color_palette[color_index]
        color_index = (color_index + 1) % len(color_palette)

    return color_dict



def is_list_of_strings(obj):
    return isinstance(obj, list) and all(isinstance(item, str) for item in obj)


def string_to_list(string_list):
    """将字符串形式的列表转换为真正的列表

    Args:
        string_list: 字符串形式的列表

    Returns:
        转换后的列表
    """

    try:
        return json.loads(string_list)
    except json.JSONDecodeError:
        print("Invalid JSON format")
        return None