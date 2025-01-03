import os
import sys



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

                    end_seconds = convert_to_seconds(end_time)
                    # ffmpeg -y -i "C:\Users\luoruofeng\Desktop\test\视频片段\Lion King 2 1998-en@cn-3.mkv" -ss 5 -vframes 1 -vf scale=320:-1 -q:v 2 "C:\Users\luoruofeng\Desktop\test\视频片段\每行截图\Lion King 2 1998-en@cn-3-1.jpg"
                    command = [
                        "ffmpeg", "-y", "-i", video, "-ss", str(end_seconds), "-vframes", "1","-q:v", "2", screenshot_path
                    ]
                    print(f"执行命令: {' '.join(command)}")
                    subprocess.run(command)
            except Exception as e:
                print(f"处理 {subdir_path} 时出错，错误: {str(e)}")
                continue  # 如果出错，跳过当前子文件夹，继续下一个

    print("所有子文件夹处理完成。")
