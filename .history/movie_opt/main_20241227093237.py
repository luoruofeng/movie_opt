import argparse
from movie_opt.commands.create import create_pc, create_phone
from movie_opt.commands.subtitle import  convert_time, srtsegment, srt2ass, addass, mergesrt, sequencesrt, srt2txtpng
from movie_opt.commands.picture import split_video, video_segment, cut_pc2phone, scale_pc2phone, add_text
from movie_opt.commands.ai import get_hard_words_and_set_color
from movie_opt.commands.translate import find_db_word
from movie_opt.commands.voice import  edge_tts_voice, gtts_voice, youdao_voice, create_mp3_by_clone_voice, clone_voice_conversion


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

    #Command subtitle -> Subcommand srtsegment
    subparser_subtitle_srtsegment = subparser_subtitle.add_parser("srtsegment", help="将srt文件根据间隔时长分段为多个srt文件")
    subparser_subtitle_srtsegment.add_argument("--path", required=True, help="srt文件的路径")
    subparser_subtitle_srtsegment.add_argument("--second", required=True, default=7 ,help="视频分段的秒数，超过这个时间就分段。")
    subparser_subtitle_srtsegment.set_defaults(func=srtsegment)

    #Command subtitle -> Subcommand convert_time
    subparser_subtitle_convert_time = subparser_subtitle.add_parser("convert_time", help="将所有srt文件的第一行字幕的开始时间改为00:00:00.000")
    subparser_subtitle_convert_time.add_argument("--path", required=True, help="包含srt文件夹的路径")
    subparser_subtitle_convert_time.set_defaults(func=convert_time)
    


    #Command picture
    parser_picture = subparsers.add_parser("picture", help="修改视频")
    subparser_picture = parser_picture.add_subparsers(dest="subcommand", help="picture命令的子命令")
    
    #Command picture -> Subcommand video_segment
    subparser_picture_video_segment = subparser_picture.add_parser("video_segment", help="根据多个srt文件的字幕时间将指定mp4切分为多个mp4片段")
    subparser_picture_video_segment.add_argument("--srt_path", required=True, help="保存srt文件的文件夹路径")
    subparser_picture_video_segment.add_argument("--video_path", required=True,help="MP4文件的路径")
    subparser_picture_video_segment.set_defaults(func=video_segment)
    
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

    #Command picture -> Subcommand split_video
    subparser_picture_split_video = subparser_picture.add_parser("split_video", help="通过视频和字幕文件生成视频中每一句的朗读视频")
    subparser_picture_split_video.add_argument("--srt_path", required=True, help="字幕文件夹的路径")
    subparser_picture_split_video.add_argument("--video_path", required=True, help="视频文件夹的路径")
    subparser_picture_split_video.set_defaults(func=split_video)

    #Command ai
    parser_ai = subparsers.add_parser("ai", help="ai提问")
    subparser_ai = parser_ai.add_subparsers(dest="subcommand", help="ai命令的子命令")
    
    # Command ai -> Subcommand get_hard_words_and_set_color
    subparser_ai_get_hard_words_and_set_color = subparser_ai.add_parser("get_hard_words_and_set_color", help="将找出txt或srt文件中某种难度的单词，默认难度4级。")
    subparser_ai_get_hard_words_and_set_color.add_argument("--path", required=True, help="txt或srt文件的路径，不能是文件夹")
    subparser_ai_get_hard_words_and_set_color.add_argument("--level", required=False, help="单词的级别，如：雅思，6级。也可以是多个级别难度：4级和6级")
    subparser_ai_get_hard_words_and_set_color.set_defaults(func=get_hard_words_and_set_color)
    
    #Command translate
    parser_translate = subparsers.add_parser("translate", help="翻译")
    subparser_translate = parser_translate.add_subparsers(dest="subcommand", help="translate命令的子命令")
    
    # Command translate -> Subcommand find_db_word
    subparser_translate_find_db_word = subparser_translate.add_parser("find_db_word", help="使用db翻译英文单词")
    subparser_translate_find_db_word.add_argument("--word", required=True, help="英文单词")
    subparser_translate_find_db_word.set_defaults(func=find_db_word)
    

    #Command voice
    parser_voice = subparsers.add_parser("voice", help="音频")
    subparser_voice = parser_voice.add_subparsers(dest="subcommand", help="voice命令的子命令")
    

    # Command voice -> Subcommand youdao_voice
    subparser_voice_youdao_voice = subparser_voice.add_parser("youdao_voice", help="将文本转化为有道发音")
    subparser_voice_youdao_voice.add_argument("--content", required=True, help="朗读内容")
    subparser_voice_youdao_voice.add_argument("--save_path", required=False, help="保存文件的路径")
    subparser_voice_youdao_voice.add_argument("--type", required=False, default=1 ,help="发音类型")
    subparser_voice_youdao_voice.set_defaults(func=youdao_voice)

    # Command voice -> Subcommand gtts_voice
    subparser_voice_gtts_voice = subparser_voice.add_parser("gtts_voice", help="将文本转化为gtts发音")
    subparser_voice_gtts_voice.add_argument("--content", required=True, help="朗读内容")
    subparser_voice_gtts_voice.add_argument("--save_path", required=False, help="保存文件的路径")
    subparser_voice_gtts_voice.add_argument("--language", required=False, default="en" ,help="语言")
    subparser_voice_gtts_voice.add_argument("--slow", required=False, default=False ,help="慢速")
    subparser_voice_gtts_voice.set_defaults(func=gtts_voice)

    # Command voice -> Subcommand edge_tts_voice
    subparser_voice_edge_tts_voice = subparser_voice.add_parser("edge_tts_voice", help="将文本转化为edge_tts发音")
    subparser_voice_edge_tts_voice.add_argument("--content", required=True, help="朗读内容")
    subparser_voice_edge_tts_voice.add_argument("--save_path", required=False, help="保存文件的路径")
    subparser_voice_edge_tts_voice.add_argument("--language", required=False, default="en" ,help="语言")
    subparser_voice_edge_tts_voice.add_argument("--voice", required=False, default=None ,help="声音")
    subparser_voice_edge_tts_voice.set_defaults(func=edge_tts_voice)

    # Command voice -> Subcommand create_mp3_by_clone_voice
    subparser_voice_create_mp3_by_clone_voice = subparser_voice.add_parser("create_mp3_by_clone_voice", help="克隆声音创建新的声音")
    subparser_voice_create_mp3_by_clone_voice.add_argument("--content", required=True, help="朗读内容")
    subparser_voice_create_mp3_by_clone_voice.add_argument("--save_path", required=False, help="保存文件的路径")
    subparser_voice_create_mp3_by_clone_voice.add_argument("--language", required=False, default="en" ,help="语言")
    subparser_voice_create_mp3_by_clone_voice.set_defaults(func=create_mp3_by_clone_voice)
    

    # Command voice -> Subcommand clone_voice_conversion
    subparser_voice_clone_voice_conversion = subparser_voice.add_parser("clone_voice_conversion", help="转化wav音频为克隆声音")
    subparser_voice_clone_voice_conversion.add_argument("--target_wav", required=True, help="需要转化的wav文件路径")
    subparser_voice_clone_voice_conversion.add_argument("--save_path", required=False, help="保存文件的路径")
    subparser_voice_clone_voice_conversion.set_defaults(func=clone_voice_conversion)
    

    # and more ...

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
