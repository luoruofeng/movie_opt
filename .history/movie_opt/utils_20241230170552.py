import json
from PIL import Image
import os
from tinytag import TinyTag
from pydub import AudioSegment
import subprocess

import subprocess
import json

def get_timescale(video_path):
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-select_streams', 'v:0', 
        '-show_entries', 'stream=time_base', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        time_base = result.stdout.strip()
        
        if not time_base:
            print("Error: time_base is empty or not found.")
            return None
        
        return time_base
    
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None
def modify_timescale(input_video_path, output_video_path, target_timescale):
    cmd = [
        'ffmpeg', 
        '-i', input_video_path, 
        '-c', 'copy',  # 保持原视频编码
        '-video_track_timescale', target_timescale,  # 设置目标时基
        output_video_path  # 输出到新文件
    ]
    
    subprocess.run(cmd, check=True)
    print(f"Timescale of {input_video_path} modified to {target_timescale}, saved as {output_video_path}")

def adjust_video_timescale(video_path1, video_path2):
    timescale1 = get_timescale(video_path1)
    if timescale1 is None:
        timescale1 = "1/1000"  # 默认值
    
    print(f"Timescale of the first video: {timescale1}")

    timescale2 = get_timescale(video_path2)
    if timescale2 is None:
        timescale2 = "1/1000"  # 默认值
    
    print(f"Timescale of the second video: {timescale2}")
    
    if timescale1 != timescale2:
        print(f"Timescale values are different, modifying the second video...")
        
        # 为输出视频创建新的文件路径
        base, ext = os.path.splitext(video_path2)
        output_video_path = base + "_modified" + ext
        
        modify_timescale(video_path2, output_video_path, timescale1)
        
        # 检查修改后的文件是否成功生成
        if os.path.exists(output_video_path):
            print(f"Modification successful. Replacing original file and deleting temporary file.")
            
            # 删除原始文件
            os.remove(video_path2)
            
            # 重命名新文件为原文件名
            os.rename(output_video_path, video_path2)
            print(f"Original file replaced with modified file.")
        else:
            print(f"Error: Modified video file does not exist.")
    else:
        print("Timescale values are the same, no modification needed.")

# 修复路径
video_path2 = "C:\\Users\\luoruofeng\\Desktop\\test\\视频片段\\每行中文视频-Lion King 2 1998-en@cn-3\\Lion King 2 1998-en@cn-3-9.mp4"
video_path1 = "C:\\Users\\luoruofeng\\Desktop\\test\\视频片段\\每行完整视频-Lion King 2 1998-en@cn-3\\Lion King 2 1998-en@cn-3-9.mp4"
# 调用函数
adjust_video_timescale(video_path1, video_path2)



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