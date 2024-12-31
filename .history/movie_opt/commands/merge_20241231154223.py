import os
import subprocess
from pathlib import Path
import re
from movie_opt.utils import *


def merge1(args):
    folder_types = [
        "每行完整视频",
        "每行中文视频",
        "每行发音视频",
        "每行发音视频2",
        "每行儿童发音视频",
        "每行跟读视频",
    ]
    merge_mp4(args, folder_types)

def merge_mp4(args, folder_types):
    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return
    

    all_video = []

    # 遍历目录及其子目录
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith(".mp4"):
                # 获取文件的绝对路径
                full_path = os.path.abspath(os.path.join(root, file))
                all_video.append(full_path)

    print(f"找到 {len(all_video)} 个 MP4 文件：")
    for video in all_video:
        print(video)

    # 子文件夹类型按顺序
    

    folder_indexs = set()
    movie_name = ""

    # 遍历文件夹
    for subdir in os.listdir(path):
        subdir_path = os.path.join(path, subdir)
        if not os.path.isdir(subdir_path):
            continue

        # 提取电影名和文件夹序号
        match = re.match(r"^(.*)-(.*)-(\d+)$", subdir)
        if not match:
            continue

        movie_name = match.group(2)
        folder_index = match.group(3)

        folder_indexs.add(folder_index)

    for folder_index in sorted(folder_indexs):
        # 创建目标输出目录
        output_dir = os.path.join(path, f"合并视频-{movie_name}-{folder_index}")
        os.makedirs(output_dir, exist_ok=True)
        
        # 定义正则表达式模式
        pattern = re.compile(rf"\\[^\\]*-(.*?)-{folder_index}\\.*\.mp4$")

        # 过滤文件路径
        same_folder_index_videos = [
            path for path in all_video if pattern.search(path)
        ]

        print(f"排序前的需要合并的视频列表：")
        for video in same_folder_index_videos:
            print(f"{video}")

        if same_folder_index_videos is None or len(same_folder_index_videos) <= 0:
            print(f"没有找到文件夹序号为{folder_index}的文件夹")
            continue

        
        # 排序后的文件列表
        sorted_videos = []

        # 定义正则表达式提取文件夹类型和视频序号
        pattern = re.compile(r".*\\(.*?)\\.*-(\d+)\.mp4$")

        # 提取信息并排序
        def extract_key(video):
            match = pattern.search(video)
            if match:
                folder_type, video_index = match.groups()
                folder_priority = folder_types.index(folder_type) if folder_type in folder_types else float('inf')
                return (int(video_index), folder_priority)
            return (float('inf'), float('inf'))  # 不匹配的项排在最后

        # 排序后的结果
        sorted_videos = sorted(same_folder_index_videos, key=extract_key)

        # 打印结果
        print("排序后的文件列表:")
        for video in sorted_videos:
            print(video)


        # 重新编码需要拼接的视频
        for video in sorted_videos:
            change_timescale(video)


        # 生成合并列表文件
        merge_list_path = os.path.join(output_dir, "merge_list.txt")
        with open(merge_list_path, "w", encoding="utf-8") as merge_list:
            for video in sorted_videos:
                merge_list.write(f"file '{video}'\n")

        # 统一音频编码和参数
        normalize_audio(sorted_videos)

        # 使用 ffmpeg 拼接视频
        output_video = os.path.join(output_dir, f"{movie_name}-{folder_index}.mp4")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", merge_list_path,
                    "-c","copy",
                    output_video,
                ],
                check=True
            )
            print(f"合并完成: {output_video}")
        except subprocess.CalledProcessError as e:
            print(f"合并失败: {output_video}")
            print(f"错误信息: {e}")

            
