import argparse
import multiprocessing
import os
import sys
import subprocess
import traceback
import shutil
from types import SimpleNamespace
import re
from movie_opt.utils import *
from movie_opt.commands.merge import delete_folders_except_merge
from movie_opt.handle import Executor
from movie_opt.config import FILTER_MORE_COUNT


@timing_decorator
def custom1(args,executor):
    if executor is None:
        logging.error("custom1 需要传入executor")
        executor = Executor()

    segment_second = args.segment_second
    if segment_second is None:
        segment_second = 13

    # 检查 args.path 是否存在且是否是文件夹
    if args is None or not os.path.exists(args.path):
        print(f"路径 {args.path} 不存在。")
        return
    if not os.path.isdir(args.path):
        print(f"{args.path} 不是一个有效的文件夹。")
        return
    
    # 循环处理文件夹内的子文件夹
    for subdir in os.listdir(args.path):
        subdir_path = os.path.join(args.path, subdir)
        try:
            # 只处理子文件夹
            if os.path.isdir(subdir_path):
                # 指定文件夹路径下的所有文件重命名为与该文件夹同名
                rename_files_to_parent_folder(subdir_path)
                #找到视频文件
                videos = find_video_files(subdir_path)
                if videos is None or len(videos) <= 0:
                    raise RuntimeError(f"{subdir_path}文件夹下没有视频文件")
                v = None
                for video in videos:
                    if str.startswith(os.path.basename(video),"subtitle_"):
                        continue
                    v = video
                    break
                #找到srt文件
                srts = find_srt_files(subdir_path)
                if srts is None or len(srts) <= 0:
                    raise RuntimeError(f"{subdir_path}文件夹下没有srt文件")
                srt = srts[0]
                convert_to_utf8(srt)
                ass = change_file_extension(srt,"ass")
                print(f"正在处理子文件夹: {subdir_path}")
                c = sys.argv[0]
                
                if not os.path.exists(os.path.join(subdir_path,"picture")):
                    print("创建封面")
                    cargs = args
                    cargs = argparse.Namespace(path=v)
                    executor.pictureOperater.generate_images(cargs)
                
                avg_word_len = executor.subtitleOperater.average_english_line_length(srt)

                if not os.path.exists(ass):
                    print("将srt字幕转化ass字幕文件")
                    cargs = args
                    cargs = argparse.Namespace(path=subdir_path)
                    executor.subtitleOperater.srt2ass(cargs)
                
                    print("修改ass复杂单词的颜色")
                    cargs = args
                    cargs = argparse.Namespace(path=ass,avg_en_word_count=avg_word_len)
                    executor.subtitleOperater.change_ass_hard_word_style(cargs)

                video_name = os.path.basename(v)
                subtitle_video_path = os.path.join(args.path,subdir, f"subtitle_{video_name}")
                
                if not os.path.exists(subtitle_video_path):
                    print("给视频添加ass字幕")
                    cargs = args
                    cargs = argparse.Namespace(path=subdir_path)
                    executor.subtitleOperater.addass(cargs)

                # 如果变量v不是以subtitle_开头，则将视频文件名改为subtitle_+视频文件名
                v_basename = os.path.basename(v)
                if not str.startswith(v_basename, "subtitle_"):
                    v = os.path.join(subdir_path,"subtitle_"+v_basename)


                if not os.path.exists(os.path.join(args.path, subdir_path,"srt分段")):
                    print("将srt文件按照时间间隔分段保存为新的srt文件")
                    cargs = args
                    cargs = argparse.Namespace(path=subdir_path,second=segment_second)
                    executor.subtitleOperater.srtsegment(cargs)
                
                # print("srt字幕内容转png图片")
                # executor.subtitleOperater.srt2txtpng(argparse.Namespace(path=subdir_path))
                # print("将srt文件按照时间间隔分段保存为新的srt文件")

                
                video_folder = os.path.join(args.path,subdir_path,"视频片段")
                if not os.path.exists(video_folder) or (os.path.exists(video_folder) and len(find_video_files(video_folder)) <= 0):
                    print("将视频分段")
                    video_extension = get_file_extension(v)
                    srt_segment_folder = os.path.join(subdir_path,"srt分段")
                    cargs = args
                    cargs = argparse.Namespace(srt_path=srt_segment_folder,video_path=v)
                    executor.pictureOperater.video_segment(cargs)
                

                # 将srt文件的第一行字幕改为00:00:00.000开始
                print("将srt文件segment时间间隔分段保存为新的srt文件")
                cargs = args
                cargs = argparse.Namespace(path=srt_segment_folder)
                executor.subtitleOperater.convert_time(cargs)

                
                # movie_opt.exe picture split_video   --srt_path="C:\Users\luoruofeng\Desktop\test\srt分段2\Lion King 2 1998-en@cn-3.srt"  --video_path="C:\Users\luoruofeng\Desktop\test\视频片段\Lion King 2 1998-en@cn-3.mkv"
                print("按照字幕行，生成视频中每一句的朗读视频和跟读视频（通过视频和字幕文件）")
                os.makedirs(os.path.join(subdir_path, "视频片段"), exist_ok=True)
                video_segment_folder = os.path.join(subdir_path, "视频片段")
                # 定义匹配文件名中序号的正则表达式
                pattern = re.compile(r"-(\d+)\.srt$")

                file_list = os.listdir(srt_segment_folder)

                srt_files_to_process = []
                for f in file_list:
                    if f.endswith(".srt"):
                        match = pattern.search(f)
                        if match:
                            srt_files_to_process.append((f, int(match.group(1))))

                srt_files_to_process.sort(key=lambda x: x[1])

                # 遍历排序后的srt文件
                for file_name, sequence in srt_files_to_process:
                    try:
                        srt_file_path = os.path.join(srt_segment_folder, file_name)
                        cargs = args
                        cargs = argparse.Namespace(avg_en_word_count=avg_word_len+FILTER_MORE_COUNT,srt_path=srt_file_path,video_path=os.path.join(video_segment_folder,get_filename_without_extension(file_name)+video_extension))
                        executor.pictureOperater.split_video(cargs)
                    except Exception as e:
                        print(f"按照字幕行，生成视频中每一句的朗读视频和跟读视频处理 {file_name} 时出错，错误: {str(e)}")
                        traceback.print_exc()
                        continue
                
                
                
                # 逐行拼接“1中英文对照 2跟读 3磨耳朵”视频
                logging.info(f"逐行拼接“1中英文对照 2跟读 3磨耳朵”视频\n{'-'*22}")
                cargs = args
                cargs = SimpleNamespace(path=video_segment_folder)
                executor.mergeOperater.merge1(cargs)
                

                # 相同编号的“1中英文对照 2跟读 3磨耳朵”视频拼接起来
                logging.info(f"相同编号的“1中英文对照 2跟读 3磨耳朵”视频拼接起来\n{'-'*22}") 
                cargs = args
                cargs = SimpleNamespace(path=video_segment_folder)
                executor.mergeOperater.merge2(cargs)


                # 将 所有“中英文对照”， 所有“跟读”， 所有“磨耳朵”视频拼接起来,形成三部完整的电影
                logging.info(f"将 所有“中英文对照”， 所有“跟读”， 所有“磨耳朵”视频拼接起来,形成三部完整的电影\n{'-'*22}")
                cargs = args
                cargs = SimpleNamespace(path=video_segment_folder)
                executor.mergeOperater.merge3(cargs) 

                # # 删除txt（拼接文件）
                # delete_txt_files(video_segment_folder)
                # # 删除其他文件夹和文件
                # delete_folders_except_merge(video_segment_folder)
            else:
                print(f"{subdir_path} 不是一个有效的文件夹。需要传入的文件夹内包含子文件夹。")
        except Exception as e:
            print(f"处理 {subdir_path} 时出错，错误: {str(e)}")
            traceback.print_exc()
            continue  # 如果出错，跳过当前子文件夹，继续下一个

    print("所有子文件夹处理完成。")


def custom2(args, executor):
    folder_path = args.path
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory.")
        return

    for item in os.listdir(folder_path):
        if item.endswith(('.mp4', '.mkv')):
            video_path = os.path.join(folder_path, item)
            video_name = os.path.splitext(item)[0]
            srt_path = os.path.join(folder_path, f"{video_name}.srt")

            if os.path.exists(srt_path):
                new_folder_path = os.path.join(folder_path, video_name)
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)

                shutil.move(video_path, new_folder_path)
                shutil.move(srt_path, new_folder_path)
                print(f"Moved {item} and {video_name}.srt to {new_folder_path}")



def custom3(args,executor):
    if executor is None:
        logging.error("custom1 需要传入executor")
        executor = Executor()

    segment_second = 11111

    # 检查 args.path 是否存在且是否是文件夹
    if args is None or not os.path.exists(args.path):
        print(f"路径 {args.path} 不存在。")
        return
    if not os.path.isdir(args.path):
        print(f"{args.path} 不是一个有效的文件夹。")
        return
    
    # 循环处理文件夹内的子文件夹
    for subdir in os.listdir(args.path):
        subdir_path = os.path.join(args.path, subdir)
        try:
            # 只处理子文件夹
            if os.path.isdir(subdir_path):
                # 指定文件夹路径下的所有文件重命名为与该文件夹同名
                rename_files_to_parent_folder(subdir_path)
                #找到视频文件
                videos = find_video_files(subdir_path)
                if videos is None or len(videos) <= 0:
                    raise RuntimeError(f"{subdir_path}文件夹下没有视频文件")
                v = None
                for video in videos:
                    if str.startswith(os.path.basename(video),"subtitle_"):
                        continue
                    v = video
                    break
                #找到srt文件
                srts = find_srt_files(subdir_path)
                if srts is None or len(srts) <= 0:
                    raise RuntimeError(f"{subdir_path}文件夹下没有srt文件")
                srt = srts[0]
                convert_to_utf8(srt)

                # srt 转为 txt
                executor.subtitleOperater.srt_2_en_txt(srt)
                executor.subtitleOperater.srt_2_txt(srt)


                ass = change_file_extension(srt,"ass")
                print(f"正在处理子文件夹: {subdir_path}")
                c = sys.argv[0]
                
                avg_word_len = executor.subtitleOperater.average_english_line_length(srt)

                if not os.path.exists(ass):
                    print("将srt字幕转化ass字幕文件")
                    cargs = args
                    cargs = argparse.Namespace(path=subdir_path)
                    executor.subtitleOperater.srt2ass(cargs)
                
                    print("修改ass复杂单词的颜色")
                    cargs = args
                    cargs = argparse.Namespace(path=ass,avg_en_word_count=avg_word_len)
                    executor.subtitleOperater.change_ass_hard_word_style(cargs)

                video_name = os.path.basename(v)
                subtitle_video_path = os.path.join(args.path,subdir, f"subtitle_{video_name}")
                
                if not os.path.exists(subtitle_video_path):
                    print("给视频添加ass字幕")
                    cargs = args
                    cargs = argparse.Namespace(path=subdir_path)
                    executor.subtitleOperater.addass(cargs)

                # 如果变量v不是以subtitle_开头，则将视频文件名改为subtitle_+视频文件名
                v_basename = os.path.basename(v)
                if not str.startswith(v_basename, "subtitle_"):
                    v = os.path.join(subdir_path,"subtitle_"+v_basename)


                if not os.path.exists(os.path.join(args.path, subdir_path,"srt分段")):
                    print("将srt文件按照时间间隔分段保存为新的srt文件")
                    cargs = args
                    cargs = argparse.Namespace(path=subdir_path,second=segment_second)
                    executor.subtitleOperater.srtsegment(cargs)
                
                # print("srt字幕内容转png图片")
                # executor.subtitleOperater.srt2txtpng(argparse.Namespace(path=subdir_path))
                # print("将srt文件按照时间间隔分段保存为新的srt文件")

                
                video_folder = os.path.join(args.path,subdir_path,"视频片段")
                if not os.path.exists(video_folder) or (os.path.exists(video_folder) and len(find_video_files(video_folder)) <= 0):
                    print("将视频分段")
                    video_extension = get_file_extension(v)
                    srt_segment_folder = os.path.join(subdir_path,"srt分段")
                    cargs = args
                    cargs = argparse.Namespace(srt_path=srt_segment_folder,video_path=v)
                    executor.pictureOperater.video_segment(cargs)
                

                # 将srt文件的第一行字幕改为00:00:00.000开始
                print("将srt文件segment时间间隔分段保存为新的srt文件")
                cargs = args
                cargs = argparse.Namespace(path=srt_segment_folder)
                executor.subtitleOperater.convert_time(cargs)

                
                # movie_opt.exe picture split_video   --srt_path="C:\Users\luoruofeng\Desktop\test\srt分段2\Lion King 2 1998-en@cn-3.srt"  --video_path="C:\Users\luoruofeng\Desktop\test\视频片段\Lion King 2 1998-en@cn-3.mkv"
                print("按照字幕行，生成视频中每一句的朗读视频和跟读视频（通过视频和字幕文件）")
                os.makedirs(os.path.join(subdir_path, "视频片段"), exist_ok=True)
                video_segment_folder = os.path.join(subdir_path, "视频片段")
                # 定义匹配文件名中序号的正则表达式
                pattern = re.compile(r"-(\d+)\.srt$")

                file_list = os.listdir(srt_segment_folder)

                srt_files_to_process = []
                for f in file_list:
                    if f.endswith(".srt"):
                        match = pattern.search(f)
                        if match:
                            srt_files_to_process.append((f, int(match.group(1))))

                srt_files_to_process.sort(key=lambda x: x[1])

                # 遍历排序后的srt文件
                for file_name, sequence in srt_files_to_process:
                    try:
                        srt_file_path = os.path.join(srt_segment_folder, file_name)
                        cargs = args
                        cargs = argparse.Namespace(avg_en_word_count=avg_word_len+FILTER_MORE_COUNT,srt_path=srt_file_path,video_path=os.path.join(video_segment_folder,get_filename_without_extension(file_name)+video_extension))
                        executor.pictureOperater.split_video(cargs)
                    except Exception as e:
                        print(f"按照字幕行，生成视频中每一句的朗读视频和跟读视频处理 {file_name} 时出错，错误: {str(e)}")
                        traceback.print_exc()
                        continue
                
                
                
                # 逐行拼接“1中英文对照 2跟读 3磨耳朵”视频
                logging.info(f"逐行拼接“1中英文对照 2跟读 3磨耳朵”视频\n{'-'*22}")
                cargs = args
                cargs = SimpleNamespace(path=video_segment_folder)
                executor.mergeOperater.merge1(cargs)
                

                # # 相同编号的“1中英文对照 2跟读 3磨耳朵”视频拼接起来
                # logging.info(f"相同编号的“1中英文对照 2跟读 3磨耳朵”视频拼接起来\n{'-'*22}") 
                # cargs = args
                # cargs = SimpleNamespace(path=video_segment_folder)
                # executor.mergeOperater.merge2(cargs)


                # # 将 所有“中英文对照”， 所有“跟读”， 所有“磨耳朵”视频拼接起来,形成三部完整的电影
                # logging.info(f"将 所有“中英文对照”， 所有“跟读”， 所有“磨耳朵”视频拼接起来,形成三部完整的电影\n{'-'*22}")
                # cargs = args
                # cargs = SimpleNamespace(path=video_segment_folder)
                # executor.mergeOperater.merge3(cargs) 

                # # 删除txt（拼接文件）
                # delete_txt_files(video_segment_folder)
                # # 删除其他文件夹和文件
                # delete_folders_except_merge(video_segment_folder)
                
                

                #将摸耳朵的mp4转换为mp3
            else:
                print(f"{subdir_path} 不是一个有效的文件夹。需要传入的文件夹内包含子文件夹。")
        except Exception as e:
            print(f"处理 {subdir_path} 时出错，错误: {str(e)}")
            traceback.print_exc()
            continue  # 如果出错，跳过当前子文件夹，继续下一个

    print("所有子文件夹处理完成。")
