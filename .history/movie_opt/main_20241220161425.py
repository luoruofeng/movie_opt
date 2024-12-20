import argparse
from movie_opt.commands.create import create_pc, create_phone
from movie_opt.commands.subtitle import srt2ass, addass, mergesrt, sequencesrt, srt2txtpng
from movie_opt.commands.picture import cut_pc2phone, scale_pc2phone, add_text
from movie_opt.commands.ai import get_hard_words_and_set_color

def main():
    parser = argparse.ArgumentParser(
        description="一个命令行工具将电影改为英语教程"
    )
    subparsers = parser.add_subparsers(dest="command", help="命令列表")

    # Command create 
    parser_create = subparsers.add_parser("create", help="通过字幕文件和视频创建新视频")
    subparser_create = parser_create.add_subparsers(dest="subcommand", help="create命令的子命令")
    
    # Command create -> Subcommand pc
    subparser_create_pc = subparser_create.add_parser("pc", help="创建pc视频")
    subparser_create_pc.add_argument("--path", required=False, help="包括了字幕和视频的文件夹的路径")
    subparser_create_pc.set_defaults(func=create_pc)

    # Command create -> Subcommand phone
    subparser_create_phone = subparser_create.add_parser("phone", help="创建phone视频")
    subparser_create_phone.add_argument("--path", required=False, help="包括了字幕和视频的文件夹的路径")
    subparser_create_phone.set_defaults(func=create_phone)

    #Command subtitle
    parser_subtitle = subparsers.add_parser("subtitle", help="格式转换")
    subparser_subtitle = parser_subtitle.add_subparsers(dest="subcommand", help="subtitle命令的子命令")
    
    # Command subtitle -> Subcommand srt2ass
    subparser_subtitle_srt2ass = subparser_subtitle.add_parser("srt2ass", help="srt -> ass 视频")
    subparser_subtitle_srt2ass.add_argument("--path", required=False, help="srt的文件夹路径")
    subparser_subtitle_srt2ass.set_defaults(func=srt2ass)

    # Command subtitle -> Subcommand mergesrt
    subparser_subtitle_mergesrt = subparser_subtitle.add_parser("mergesrt", help="将两个不同语言的srt合并为一个srt")
    subparser_subtitle_mergesrt.add_argument("--path", required=False, help="srt的文件夹路径")
    subparser_subtitle_mergesrt.set_defaults(func=mergesrt)
    

    # Command subtitle -> Subcommand addass
    subparser_subtitle_addass = subparser_subtitle.add_parser("addass", help="ass字幕添加到视频")
    subparser_subtitle_addass.add_argument("--path", required=False, help="ass的文件夹路径")
    subparser_subtitle_addass.set_defaults(func=addass)

    # Command subtitle -> Subcommand sequencesrt
    subparser_subtitle_sequencesrt = subparser_subtitle.add_parser("sequencesrt", help="顺序显示每一行srt字幕")
    subparser_subtitle_sequencesrt.add_argument("--path", required=False, help="ass的文件夹路径")
    subparser_subtitle_sequencesrt.set_defaults(func=sequencesrt)

    #Command subtitle -> Subcommand srt2txtpng
    subparser_subtitle_srt2txtpng = subparser_subtitle.add_parser("srt2txtpng", help="将pc尺寸的视频缩放为手机大小的视频")
    subparser_subtitle_srt2txtpng.add_argument("--path", required=False, help="视频文件夹的路径")
    subparser_subtitle_srt2txtpng.set_defaults(func=srt2txtpng)

    

    #Command picture
    parser_picture = subparsers.add_parser("picture", help="修改视频")
    subparser_picture = parser_picture.add_subparsers(dest="subcommand", help="picture命令的子命令")
    
    # Command picture -> Subcommand cut_pc2phone
    subparser_picture_cut_pc2phone = subparser_picture.add_parser("cut_pc2phone", help="将pc尺寸的视频裁剪为手机大小的视频")
    subparser_picture_cut_pc2phone.add_argument("--path", required=False, help="视频文件夹的路径")
    subparser_picture_cut_pc2phone.set_defaults(func=cut_pc2phone)

    #Command picture -> Subcommand scale_pc2phone
    subparser_picture_scale_pc2phone = subparser_picture.add_parser("scale_pc2phone", help="将pc尺寸的视频缩放为手机大小的视频")
    subparser_picture_scale_pc2phone.add_argument("--path", required=False, help="视频文件夹的路径")
    subparser_picture_scale_pc2phone.set_defaults(func=scale_pc2phone)

    #Command picture -> Subcommand add_text
    subparser_picture_add_text = subparser_picture.add_parser("add_text", help="将pc尺寸的视频缩放为手机大小的视频")
    subparser_picture_add_text.add_argument("--path", required=False, help="视频文件夹的路径")
    subparser_picture_add_text.set_defaults(func=add_text)

    #Command ai
    parser_ai = subparsers.add_parser("ai", help="ai提问")
    subparser_ai = parser_ai.add_subparsers(dest="subcommand", help="ai命令的子命令")
    
    # Command ai -> Subcommand get_hard_words_and_set_color
    subparser_ai_get_hard_words_and_set_color = subparser_ai.add_parser("get_hard_words_and_set_color", help="将找出txt或srt文件中某种难度的单词，默认难度4级。")
    subparser_ai_get_hard_words_and_set_color.add_argument("--path", required=True, help="txt或srt文件的路径，不能是文件夹")
    subparser_ai_get_hard_words_and_set_color.add_argument("--level", required=False, help="单词的级别，如：雅思，6级。也可以是多个级别难度：4级和6级")
    subparser_ai_get_hard_words_and_set_color.set_defaults(func=get_hard_words_and_set_color)
    

    # and more ...

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
