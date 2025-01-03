import os
import sys
import subprocess


def custom1(args):
    # 检查 args.path 是否存在且是否是文件夹
    if not os.path.exists(args.path):
        print(f"路径 {args.path} 不存在。")
        return
    if not os.path.isdir(args.path):
        print(f"{args.path} 不是一个有效的文件夹。")
        return

    # 循环处理文件夹内的子文件夹
    for subdir in os.listdir(args.path):
        subdir_path = os.path.join(args.path, subdir)

        # 只处理子文件夹
        if os.path.isdir(subdir_path):
            try:
                print(f"正在处理子文件夹: {subdir_path}")
                c = sys.argv[0]
                command = [
                    c,
                    "subtitle", 
                    "srt2ass", 
                    "--path="+subdir_path
                ]
                print("将srt字幕转化ass字幕文件")
                print(f"执行命令: {' '.join(command)}")
                subprocess.run(command)
            except Exception as e:
                print(f"处理 {subdir_path} 时出错，错误: {str(e)}")
                continue  # 如果出错，跳过当前子文件夹，继续下一个

    print("所有子文件夹处理完成。")
