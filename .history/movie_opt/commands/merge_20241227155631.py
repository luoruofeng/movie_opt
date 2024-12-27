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

    # 子文件夹类型按顺序
    folder_types = [
        "每行完整视频",
        "每行中文视频",
        "每行发音视频",
        "每行发音视频2",
        "每行儿童发音视频",
        "每行跟读视频",
    ]

    folder_index = set()

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

        # 创建目标输出目录
        output_dir = os.path.join(path, f"合并视频-{movie_name}-{folder_index}")
        os.makedirs(output_dir, exist_ok=True)

        # 按类型顺序处理视频文件
        for folder_type in folder_types:
            folder_path = os.path.join(subdir_path, folder_type)
            if not os.path.exists(folder_path):
                print(f"子文件夹缺失，跳过: {folder_path}")
                continue

            # 获取所有 MP4 文件，按序号排序
            mp4_files = []
            for file in os.listdir(folder_path):
                if file.endswith(".mp4") and file.startswith(f"{movie_name}-{folder_index}"):
                    try:
                        seq_num = int(file.split("-")[-1].split(".")[0])
                        mp4_files.append((seq_num, os.path.join(folder_path, file)))
                    except ValueError:
                        print(f"文件命名不规范，跳过: {file}")

            # 按序号排序
            mp4_files.sort()

            # 检查是否有缺失序号
            expected_seq = 1
            ordered_files = []
            for seq_num, file_path in mp4_files:
                if seq_num == expected_seq:
                    ordered_files.append(file_path)
                    expected_seq += 1
                else:
                    print(f"缺少序号 {expected_seq}，跳过该视频。")
                    break

            if not ordered_files:
                print(f"没有可用的视频文件，跳过文件夹: {folder_path}")
                continue

            # 创建临时文件列表用于 ffmpeg
            temp_file_list = os.path.join(output_dir, "file_list.txt")
            with open(temp_file_list, "w", encoding="utf-8") as f:
                for file_path in ordered_files:
                    f.write(f"file '{file_path}'\n")

            # 合并视频
            output_file = os.path.join(output_dir, f"{folder_type}.mp4")
            command = [
                "ffmpeg", "-f", "concat", "-safe", "0", "-i", temp_file_list,
                "-c", "copy", output_file
            ]

            try:
                subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"合并完成: {output_file}")
            except subprocess.CalledProcessError as e:
                print(f"合并失败: {output_file}\n错误信息: {e.stderr.decode('utf-8')}")

            # 删除临时文件
            os.remove(temp_file_list)

