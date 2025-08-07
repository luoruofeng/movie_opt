import os
import subprocess
import torch
import re
from movie_opt.utils import *
from pkg_resources import resource_filename
import logging
import shutil
from movie_opt.commands.ai import LaunageAI


def delete_folders_except_merge(folder_path):
    """
    遍历删除指定文件夹下的所有子文件夹和文件，保留以“合并视频-”开头的文件夹。

    :param folder_path: 要操作的文件夹路径
    """
    if not os.path.exists(folder_path):
        print(f"路径不存在: {folder_path}")
        return
    
    # 获取当前文件夹中的所有子文件夹和文件
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        
        if os.path.isdir(item_path):
            # 如果是文件夹且名字不是以“合并视频-”开头，则删除
            if not item.startswith("合并视频-"):
                try:
                    shutil.rmtree(item_path)  # 删除整个文件夹及其内容
                    logging.info(f"删除文件夹及内容: {item_path}")
                except Exception as e:
                    logging.error(f"无法删除文件夹 {item_path}: {e}")
        elif os.path.isfile(item_path):
            # 删除当前文件夹下的文件
            try:
                os.remove(item_path)
                logging.info(f"删除文件: {item_path}")
            except Exception as e:
                logging.error(f"无法删除文件 {item_path}: {e}")


def sort_paths_by_last_number(paths):
    """
    根据文件名最后一个“-”后的数字对路径列表进行排序。
    将数字从字符串转换为整数以进行比较，正序排列。

    :param paths: 包含绝对路径的列表。
    :return: 排序后的列表。
    """
    def extract_last_number(path):
        """
        从路径的文件名中提取最后一个“-”后的数字并返回其整数值。
        """
        file_name = os.path.basename(path)  # 提取文件名
        if "-" in file_name:
            try:
                number_part = file_name.split("-")[-1]  # 获取最后一个“-”后的部分
                number = int(os.path.splitext(number_part)[0])  # 去掉扩展名并转为整数
                return number
            except ValueError:
                pass  # 如果无法转换为整数，忽略此文件名中的数字部分
        return float('inf')  # 如果无数字，放在排序的末尾

    # 按提取的数字排序
    return sorted(paths, key=extract_last_number)



def find_videos_in_special_folders(directory,dir_suffix="-中英对照"):
    """
    查找指定文件夹下所有子文件夹，子文件夹名字以“合并视频-”开头并以“-中英对照”结尾。
    如果这些子文件夹下有视频文件，则将这些视频文件的绝对路径放入数组并返回。

    :param directory: 指定的文件夹路径。
    :return: 包含符合条件的视频文件绝对路径的数组。
    """
    video_extensions = {".mp4", ".mkv", ".avi", ".mov", ".flv"}  # 常见视频文件扩展名
    video_paths = []

    # 遍历指定目录下的所有子文件夹
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            # 检查子文件夹名字是否符合条件
            if dir_name.startswith("合并视频-") and dir_name.endswith(dir_suffix):
                folder_path = os.path.join(root, dir_name)
                
                # 遍历该子文件夹下的所有文件
                for file_name in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file_name)
                    
                    # 检查文件是否为视频文件
                    if os.path.isfile(file_path) and os.path.splitext(file_name)[1].lower() in video_extensions:
                        video_paths.append(os.path.abspath(file_path))
    
    return video_paths

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

def merge_same_type(args,dir_suffix="-中英对照"):
    dir_path = args.path
    video_output_dir = os.path.join(dir_path, "合并视频-从头到尾")
    video_name = dir_suffix.split("-")[-1]
    if not os.path.exists(video_output_dir):
        os.makedirs(video_output_dir, exist_ok=True)
    merge_list_path = os.path.join(video_output_dir , f"merge_list.txt")
    videos = sort_paths_by_last_number(find_videos_in_special_folders(dir_path,dir_suffix))
    if videos == None or len(videos) <= 0:
        print(f"没有找到视频: {dir_path}")
        logging.info(f"没有找到视频: {dir_path}")
        return
    # 创建合并列表文件
    file_extension = get_file_extension(videos[0])
    with open(merge_list_path, "w", encoding="utf-8") as merge_list:
        for v in videos:
            merge_list.write(f"file '{v}'\n")
    # 使用 ffmpeg 拼接视频
    output_video = os.path.join(video_output_dir, f"{video_name}.{file_extension}")
    print(f"开始合成从头到尾视频 output_video: {output_video} videos:{videos}")
    logging.info(f"开始合成从头到尾视频 output_video: {output_video} videos:{videos}")
    try:
        command = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", merge_list_path,
                "-c","copy",
                output_video,
            ]
        print(" ".join(command))
        subprocess.run(
            command,
            check=True
        )
        print(f"合并从头到尾视频完成: {output_video}")
        return output_video
    except subprocess.CalledProcessError as e:
        print(f"错误信息: {e}")
        logging.error(f"merge3 合并失败: {output_video} 错误信息: {e}")
    
def merge_diff_type(args,type):
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

    # 合并视频-最终
    if type == 4:
        if args.cnen_c is None or len(args.cnen_c) <= 0:
            print("中英对照内容不能为空")
            return
        
        if args.ear_c is None or len(args.ear_c) <= 0:
            print("磨耳朵内容不能为空")
            return
        
        # if args.follow_c is None or len(args.follow_c) <= 0:
        #     print("跟读内容不能为空")
        #     return
        

        file_extension = get_file_extension(args.cnen_c[0])

        cnen_h = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "中英对照横屏"+file_extension)
        ear_h = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "磨耳朵横屏"+file_extension)
        # follow_h = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "跟读横屏"+file_extension)
        
        output_dir = os.path.join(args.path, "合并视频-最终")
        os.makedirs(output_dir, exist_ok=True)


        for v in args.cnen_c:
            video_index = int(get_filename_without_extension(v).split("-")[-1])
            
            ear_c = get_file_by_suffix_number(args.ear_c,video_index)
            # follow_c = get_file_by_suffix_number(args.follow_c,video_index)
            cnen_c = get_file_by_suffix_number(args.cnen_c,video_index)
            
            if cnen_c is None or len(cnen_c) <= 0:
                print("中英对照内容不能为空!")
                return
            
            if ear_c is None or len(ear_c) <= 0:
                print("磨耳朵内容不能为空!")
                return
            
            # if follow_c is None or len(follow_c) <= 0:
            #     print("跟读内容不能为空!")
            #     return
            
            # 将内容视频的长宽改为头视频的长款才能拼接
            w,h = get_video_w_h(cnen_h)
            resize_video(cnen_c,w,h)
            # resize_video(follow_c,w,h)
            resize_video(ear_c,w,h)

            merge_video = [cnen_h, cnen_c, ear_h, ear_c]
            logging.info(f"merge_video:{merge_video}")
            video_extension = get_file_extension(cnen_c)

            video_output_dir = os.path.join(output_dir, str(video_index))
            os.makedirs(video_output_dir, exist_ok=True)
            merge_list_path = os.path.join(video_output_dir , f"merge_list-{video_index}.txt")
            with open(merge_list_path, "w", encoding="utf-8") as merge_list:
                for mv in merge_video:
                    merge_list.write(f"file '{mv}'\n")

            # TODO
            # 修改视频的时间戳timescale，保证视频拼接后不卡顿
            for video in merge_video:
                change_timescale(video,file_extension=video_extension)
            # 统一音频编码和参数，保证视频拼接后有声音
            normalize_audio(merge_video)

            # 使用 ffmpeg 拼接视频
            output_video = os.path.join(video_output_dir, f"{video_index}{video_extension}")
            try:
                command = [
                        "ffmpeg",
                        "-f", "concat",
                        "-safe", "0",
                        "-i", merge_list_path,
                        "-c","copy",
                        output_video,
                    ]
                print(" ".join(command))
                subprocess.run(
                    command,
                    check=True
                )
                print(f"合并最终视频完成: {output_video}")
            except subprocess.CalledProcessError as e:
                print(f"错误信息: {e}")
                logging.error(f"merge2 合并失败: {output_video} 错误信息: {e}")
                continue

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
            if file.lower().endswith(".mp4") or file.lower().endswith(".mkv") :
                # 获取文件的绝对路径
                full_path = os.path.abspath(os.path.join(root, file))
                all_video.append(full_path)

    print(f"{path} 找到 {len(all_video)} 个 视频 文件：")
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
        output_dir = os.path.join(path, f"合并视频-{video_type}-{folder_index}")
        os.makedirs(output_dir, exist_ok=True)
        
        # 定义正则表达式模式
        pattern = re.compile(rf"\\[^\\]*-(.*?)-{folder_index}\\.*\..*$")

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
        pattern = re.compile(r".*\\(.*?)-.*\\.*-(\d+)\..*$")

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

        if len(sorted_videos) <= 0:
            print(f"没有找到文件夹序号为{folder_index}的文件夹")
            logging.info(f"没有找到文件夹序号为{folder_index}的文件夹")
            continue

        video_extension = get_file_extension(sorted_videos[0])

        # 修改视频的时间戳timescale，保证视频拼接后不卡顿
        for video in sorted_videos:
            change_timescale(video)
        # 统一音频编码和参数，保证视频拼接后有声音
        normalize_audio(sorted_videos)

        # 使用 ffmpeg 拼接视频
        output_video = os.path.join(output_dir, f"{movie_name}-{folder_index}{video_extension}")
        try:
            if torch.cuda.is_available():
                video_codec = "h264_nvenc"
            else:
                video_codec = "libx264"
            command = [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", merge_list_path,
                    "-c:v", video_codec,
                    "-c:a", "copy",
                    output_video
                ]
            print(" ".join(command))
            subprocess.run(
                command,
                check=True
            )
            print(f"合并每行完成: {output_video}")
        except subprocess.CalledProcessError as e:
            print(f"合并失败: {output_video}")
            print(f"错误信息: {e}")
        
        r_paths.append(output_video)
    return r_paths


class MergeOperater:
    def __init__(self,launageAI):
        self.launageAI:LaunageAI = launageAI


    def merge1(self,args):
        cnen_c = merge_diff_type(args,1)
        logging.info(f"merge1:逐行拼接“中英文对照”视频完成 {cnen_c}")

        # follow_c = merge_diff_type(args,2)
        # logging.info(f"merge1:逐行拼接“跟读”视频完成 {follow_c}")
        
        ear_c = merge_diff_type(args,3)
        logging.info(f"merge1:逐行拼接“磨耳朵”视频完成 {args.path}\n{ear_c}")
        

    def merge2(self,args):
        dir_path = args.path
        args.cnen_c = sort_paths_by_last_number(find_videos_in_special_folders(dir_path,"-中英对照"))
        # args.follow_c = sort_paths_by_last_number(find_videos_in_special_folders(dir_path,"-跟读"))
        args.ear_c = sort_paths_by_last_number(find_videos_in_special_folders(dir_path,"-磨耳朵"))
        merge_diff_type(args,4)
        logging.info(f"merge2:相同编号的“1中英文对照 2跟读 3磨耳朵”视频拼接起来完成 {args.path}")

    def merge3(self,args):
        merge_same_type(args,"-中英对照")
        # merge_same_type(args,"-跟读")
        merge_same_type(args,"-磨耳朵")
        


