import os
import subprocess
from pathlib import Path
import re

def merge_mp4(args):
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
    folder_types = [
        "每行完整视频",
        "每行中文视频",
        "每行发音视频",
        "每行发音视频2",
        "每行儿童发音视频",
        "每行跟读视频",
    ]

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

        # 按类型顺序处理视频文件
        for folder_type in folder_types:
        
        
            
