import os
import subprocess
from pathlib import Path
import re
from movie_opt.utils import *
from pkg_resources import resource_filename

import os

def extract_parts(file_path: str):
    """
    提取路径中最后一个 `-` 后的数字和最后一级文件夹中第一个 `-` 前的内容。
    
    :param file_path: 文件路径字符串
    :return: 包含两个提取结果的元组 (最后一个 `-` 后的数字, 文件夹名字第一个 `-` 前的内容)
    """
    # 获取文件名
    file_name = os.path.basename(file_path)
    # 获取所在的最后一级文件夹
    last_folder = os.path.basename(os.path.dirname(file_path))
    
    try:
        # 提取最后一个 `-` 后的数字
        last_dash_index = file_name.rfind('-')
        number = file_name[last_dash_index + 1:].split('.')[0]
        
        # 提取最后一级文件夹中第一个 `-` 前的部分
        first_dash_index = last_folder.find('-')
        folder_part = last_folder[:first_dash_index] if first_dash_index != -1 else last_folder
        
        return int(number), folder_part
    except Exception as e:
        raise ValueError(f"无法提取路径中的部分信息: {e}")


def filter_videos1(same_folder_index_videos: list):
    """
    根据提取的 ID 和文件夹规则来过滤视频列表：
    如果同一视频 ID 同时出现在 '每行完整视频' 和 '每行分段视频' 中，则删除 '每行分段视频' 的项。
    
    :param same_folder_index_videos: 视频文件路径列表
    :return: 处理后的视频路径列表
    """
    video_map = {}  # 存储视频ID对应的文件夹类型
    result = []

    # 遍历视频列表，提取视频ID和文件夹名称
    for video_path in same_folder_index_videos:
        video_id, folder_part = extract_parts(video_path)
        
        if video_id not in video_map:
            video_map[video_id] = []
        
        video_map[video_id].append(folder_part)
    
    # 遍历并构建新的列表
    for video_path in same_folder_index_videos:
        video_id, folder_part = extract_parts(video_path)
        
        # 检查该视频ID的文件夹类型
        if video_id in video_map:
            if "每行完整视频" in video_map[video_id] and "每行分段视频" in video_map[video_id] and len(video_map[video_id]) == 2:
                # 如果同时包含 '每行完整视频' 和 '每行分段视频',并且只有这两个数据，只保留 '每行完整视频'
                if folder_part == "每行分段视频":
                    continue  # 跳过 '每行分段视频' 的项
            # 保留其他情况
        result.append(video_path)
    
    return result


def get_file_by_suffix_number(file_paths, target_number):
    """
    从文件路径列表中找到文件名包含特定后缀的文件绝对路径。

    :param file_paths: list 文件绝对路径列表
    :param target_number: int 目标数字，用于匹配文件名中的 -<数字>
    :return: str 匹配的文件绝对路径，若无匹配则返回 None
    """
    target_suffix = f"-{target_number}"
    for file_path in file_paths:
        # 获取文件名（不带路径）
        file_name_without_extension = get_filename_without_extension(file_path)
        if file_name_without_extension.endswith(target_suffix):
            return file_path
    return None

def merge1(args):
    cnen_c = merge1_diff_type(args,1)
    follow_c = merge1_diff_type(args,2)
    ear_c = merge1_diff_type(args,3)

    # args.cnen_c = cnen_c
    # args.follow_c = follow_c
    # args.ear_c = ear_c
    # r_path = merge1_diff_type(args,4)

def merge1_diff_type(args,type):
    if type == 1:
        folder_types = [
            "每行完整视频",
            "每行中文视频",
            "每行儿童发音视频",
        ]
        return merge_mp4(args, folder_types,"中英对照")

    if type == 2:
        folder_types = [
            "每行分段视频",
            "每行跟读视频"
        ]
        return merge_mp4(args, folder_types,"跟读")

    if type == 3:
        folder_types = [
            "每行分段视频",
            "每行发音视频",
            "每行发音视频2",
            "每行儿童发音视频"
        ]
        return merge_mp4(args, folder_types,"磨耳朵")

    if type == 4:
        if args.cnen_c is None or len(args.cnen_c) <= 0:
            print("中英对照内容不能为空")
            return
        
        if args.ear_c is None or len(args.ear_c) <= 0:
            print("磨耳朵内容不能为空")
            return
        
        if args.follow_c is None or len(args.follow_c) <= 0:
            print("跟读内容不能为空")
            return

        cnen_h = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "中英对照横屏.mp4")
        ear_h = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "磨耳朵横屏.mp4")
        follow_h = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "跟读横屏.mp4")
        
        output_dir = os.path.join(args.path, "合并视频-最终")
        os.makedirs(output_dir, exist_ok=True)


        for v in args.cnen_c:
            video_index = int(get_filename_without_extension(v).split("-")[-1])
            
            ear_c = get_file_by_suffix_number(args.ear_c,video_index)
            follow_c = get_file_by_suffix_number(args.follow_c,video_index)
            cnen_c = get_file_by_suffix_number(args.cnen_c,video_index)
            
            if cnen_c is None or len(cnen_c) <= 0:
                print("中英对照内容不能为空!")
                return
            
            if ear_c is None or len(ear_c) <= 0:
                print("磨耳朵内容不能为空!")
                return
            
            if follow_c is None or len(follow_c) <= 0:
                print("跟读内容不能为空!")
                return
            
            # 将内容视频的长宽改为头视频的长款才能拼接
            w,h = get_video_w_h(cnen_h)
            resize_video(cnen_c,w,h)
            resize_video(follow_c,w,h)
            resize_video(ear_c,w,h)

            merge_video = [cnen_h, cnen_c, follow_h, follow_c, ear_h, ear_c]

            video_output_dir = os.path.join(output_dir, str(video_index))
            os.makedirs(video_output_dir, exist_ok=True)
            merge_list_path = os.path.join(video_output_dir , f"merge_list-{video_index}.txt")
            with open(merge_list_path, "w", encoding="utf-8") as merge_list:
                for mv in merge_video:
                    merge_list.write(f"file '{mv}'\n")

            # 修改视频的时间戳timescale，保证视频拼接后不卡顿
            for video in merge_video:
                change_timescale(video)


            # 统一音频编码和参数，保证视频拼接后有声音
            normalize_audio(merge_video)

            # 使用 ffmpeg 拼接视频
            output_video = os.path.join(video_output_dir, f"{video_index}.mp4")
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
            return output_video


def merge_mp4(args, folder_types, video_type):
    r_paths = []
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

    print(f"{path} 找到 {len(all_video)} 个 MP4 文件：")
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
        output_dir = os.path.join(path, f"合并视频-{movie_name}-{folder_index}-{video_type}")
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
        pattern = re.compile(r".*\\(.*?)-.*\\.*-(\d+)\.mp4$")

        # 如果 video 不在 folder_types 范围中，删除该元素
        filtered_videos = []
        for v in same_folder_index_videos:
            match = pattern.search(v)
            if match:
                folder_type, _ = match.groups()
                if folder_type in folder_types:
                    filtered_videos.append(v)
        same_folder_index_videos = filtered_videos


                

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

        # 如果同一视频 ID 同时出现在 '每行完整视频' 和 '每行分段视频' 中，则删除 '每行分段视频' 的项。
        sorted_videos = filter_videos1(sorted_videos)
        
        # 打印结果
        print("删除不必要的元素后的文件列表:")
        for video in sorted_videos:
            print(video)


        # 生成合并列表文件
        merge_list_path = os.path.join(output_dir, "merge_list.txt")
        with open(merge_list_path, "w", encoding="utf-8") as merge_list:
            for video in sorted_videos:
                merge_list.write(f"file '{video}'\n")

        # 修改视频的时间戳timescale，保证视频拼接后不卡顿
        for video in sorted_videos:
            change_timescale(video)


        # 统一音频编码和参数，保证视频拼接后有声音
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
        
        r_paths.append(output_video)
    return r_paths
