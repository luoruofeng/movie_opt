import json
from PIL import Image
import os
from tinytag import TinyTag
from pydub import AudioSegment
import subprocess


def fix_video_timestamps(video_path):
    """
    Check if the video requires timestamp fixes and repair them if necessary.

    Parameters:
        video_path (str): Path to the video to be checked and repaired.

    Returns:
        bool: True if timestamps were fixed, False otherwise.
    """
    try:
        # Check video stream for timestamp issues using ffprobe
        ffprobe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "packet=dts", 
            "-select_streams", "v", "-of", "csv", video_path
        ]
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)

        # Analyze DTS values for irregularities
        dts_values = [int(line.split(',')[1]) for line in result.stdout.splitlines() if ',' in line]
        if not dts_values or sorted(dts_values) == dts_values:
            print("No timestamp issues detected. No fixes needed.")
            return False

        print("Timestamp irregularities detected. Proceeding with fixes.")

        # Temporary output path
        temp_output = os.path.splitext(video_path)[0] + "_fixed.mp4"

        # Fix timestamps using FFmpeg
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", video_path,
            "-fflags", "+genpts",
            "-vsync", "vfr",
            "-c", "copy",
            temp_output
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # Replace the original video with the fixed one
        os.replace(temp_output, video_path)
        print(f"Timestamps fixed and updated: {video_path}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

# Example usage
video_path = "path/to/video.mp4"
fix_video_timestamps(video_path)

def reencode_video_to_match(input_video_1, input_video_2):
    """
    Re-encode the second video to match the encoding parameters of the first video if necessary.

    Parameters:
        input_video_1 (str): Path to the first video (source of encoding parameters).
        input_video_2 (str): Path to the second video (to be re-encoded).

    Returns:
        bool: True if re-encoding and replacement succeeded, False if not needed or failed.
    """
    try:
        # Use FFprobe to extract encoding parameters for both videos
        def get_encoding_info(video_path):
            ffprobe_cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", 
                "stream=codec_name,profile,level,pix_fmt", "-of", "json", video_path
            ]
            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
            return result.stdout

        encoding_info_1 = get_encoding_info(input_video_1)
        encoding_info_2 = get_encoding_info(input_video_2)

        # Compare encoding parameters
        if encoding_info_1 == encoding_info_2:
            print("The videos have matching encoding parameters. No re-encoding needed.")
            return False
        else:
            print(f"需要重新编码视频{input_video_2} 编码信息{encoding_info_2}")

        # Temporary output path for the re-encoded second video
        temp_output = "temp_reencoded_video.mp4"

        # Use FFmpeg to re-encode the second video to match the first video's parameters
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", input_video_2,  # Input second video
            "-c:v", "libx264",    # Match video codec
            "-preset", "fast",    # Encoding speed/quality balance
            "-crf", "23",         # Quality setting (constant rate factor)
            "-c:a", "aac",         # Match audio codec
            "-b:a", "128k",       # Audio bitrate
            temp_output             # Output re-encoded video
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # Replace the original second video with the re-encoded one
        os.replace(temp_output, input_video_2)
        print(f"Successfully re-encoded and replaced: {input_video_2}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

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