def merge_mp4(args):  
    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return


    screenshots_dir = os.path.join(os.path.dirname(video), "每行截图-"+video_name)
    os.makedirs(screenshots_dir, exist_ok=True)