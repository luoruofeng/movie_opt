import json
from PIL import Image
import os
from tinytag import TinyTag
from pydub import AudioSegment
import subprocess
import shlex
from datetime import datetime, timedelta


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



def change_timescale(video_path, timescale=1000):
    # 判断当前视频的 timescale 是否已经是目标值
    temp_video_path = 'temp.mp4'
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
        # 调用 ffprobe 获取视频时长
        command = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=duration", "-of", "csv=p=0", file_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe 执行失败: {result.stderr.strip()}")
        
        # 解析时长并保留 3 位小数
        duration = float(result.stdout.strip())
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