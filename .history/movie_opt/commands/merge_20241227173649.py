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
        
        # 筛选匹配的 MP4 文件
        same_folder_index_videos = [
            video for video in all_video
            if re.search(rf"{re.escape(movie_name)}-\d+/{movie_name}-\d+\.mp4$", video) and re.search(rf"-{folder_index}/", video)
        ]

        #操作same_folder_index_videos, 根据video_index，folder_types正序排列，然后拼接视频
                
        # 按 folder_types 的顺序对视频进行排序
        sorted_videos = []
        for folder_type in folder_types:
            # 按文件路径中包含的 folder_type 进行筛选
            sorted_videos.extend(
                [video for video in same_folder_index_videos if folder_type in video]
            )

        # 如果某些视频未匹配到 folder_types，则保持它们原有顺序
        remaining_videos = [
            video for video in same_folder_index_videos if video not in sorted_videos
        ]
        sorted_videos.extend(remaining_videos)
        
        print(f"排序后的需要合并的视频列表：{sorted_videos}")

        # 生成合并列表文件
        merge_list_path = os.path.join(output_dir, "merge_list.txt")
        with open(merge_list_path, "w", encoding="utf-8") as merge_list:
            for video in sorted_videos:
                merge_list.write(f"file '{video}'\n")

        # 使用 ffmpeg 拼接视频
        output_video = os.path.join(output_dir, f"{movie_name}-{folder_index}.mp4")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", merge_list_path,
                    "-c", "copy",
                    output_video,
                ],
                check=True
            )
            print(f"合并完成: {output_video}")
        except subprocess.CalledProcessError as e:
            print(f"合并失败: {output_video}")
            print(f"错误信息: {e}")

            
