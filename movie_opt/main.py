import logging

def setup_logging():
    logging.basicConfig(
        filename='movie_opt.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8'
    )

setup_logging()

import argparse
from movie_opt.commands.create import create_pc, create_phone
from movie_opt.commands.translate import find_db_word
from movie_opt.commands.pdf import pdf_to_txt_pdfplumber, split_sentences_2voice
from movie_opt.commands.custom import custom1
from movie_opt.handle import Executor

def main():
    executor = Executor()
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
    subparser_subtitle_srt2ass.set_defaults(func=executor.subtitleOperater.srt2ass)

    # Command subtitle -> Subcommand reposition_srt
    subparser_subtitle_reposition_srt = subparser_subtitle.add_parser("reposition_srt", help="将英文的srt文件中的英文重新排版")
    subparser_subtitle_reposition_srt.add_argument("--path", required=False, help="srt的文件夹路径")
    subparser_subtitle_reposition_srt.set_defaults(func=executor.subtitleOperater.reposition_srt)

    # Command subtitle -> Subcommand ass_to_srt
    subparser_subtitle_ass_to_srt = subparser_subtitle.add_parser("ass_to_srt", help="将ass转化为srt")
    subparser_subtitle_ass_to_srt.add_argument("--path", required=False, help="srt的文件夹路径")
    subparser_subtitle_ass_to_srt.set_defaults(func=executor.subtitleOperater.ass_to_srt)

    
    # Command subtitle -> Subcommand change_ass_hard_word_style
    subparser_subtitle_change_ass_hard_word_style = subparser_subtitle.add_parser("change_ass_hard_word_style", help="ass文件的复杂单词修改颜色样式")
    subparser_subtitle_change_ass_hard_word_style.add_argument("--path", required=False, help="ass的文件夹路径")
    subparser_subtitle_change_ass_hard_word_style.set_defaults(func=executor.subtitleOperater.change_ass_hard_word_style)


    # Command subtitle -> Subcommand mergesrt
    subparser_subtitle_mergesrt = subparser_subtitle.add_parser("mergesrt", help="将两个不同语言的srt合并为一个srt")
    subparser_subtitle_mergesrt.add_argument("--path", required=False, help="srt的文件夹路径")
    subparser_subtitle_mergesrt.set_defaults(func=executor.subtitleOperater.mergesrt)
    

    # Command subtitle -> Subcommand addass
    subparser_subtitle_addass = subparser_subtitle.add_parser("addass", help="ass字幕添加到视频")
    subparser_subtitle_addass.add_argument("--path", required=False, help="ass的文件夹路径")
    subparser_subtitle_addass.set_defaults(func=executor.subtitleOperater.addass)

    # Command subtitle -> Subcommand sequencesrt
    subparser_subtitle_sequencesrt = subparser_subtitle.add_parser("sequencesrt", help="顺序显示每一行srt字幕")
    subparser_subtitle_sequencesrt.add_argument("--path", required=False, help="ass的文件夹路径")
    subparser_subtitle_sequencesrt.set_defaults(func=executor.subtitleOperater.sequencesrt)

    #Command subtitle -> Subcommand srt2txtpng
    subparser_subtitle_srt2txtpng = subparser_subtitle.add_parser("srt2txtpng", help="将pc尺寸的视频缩放为手机大小的视频")
    subparser_subtitle_srt2txtpng.add_argument("--path", required=False, help="视频文件夹的路径")
    subparser_subtitle_srt2txtpng.set_defaults(func=executor.subtitleOperater.srt2txtpng)

    #Command subtitle -> Subcommand srtsegment
    subparser_subtitle_srtsegment = subparser_subtitle.add_parser("srtsegment", help="将srt文件根据间隔时长分段为多个srt文件")
    subparser_subtitle_srtsegment.add_argument("--path", required=True, help="srt文件的路径")
    subparser_subtitle_srtsegment.add_argument("--second", required=True, default=7 ,help="视频分段的秒数，超过这个时间就分段。")
    subparser_subtitle_srtsegment.set_defaults(func=executor.subtitleOperater.srtsegment)

    #Command subtitle -> Subcommand convert_time
    subparser_subtitle_convert_time = subparser_subtitle.add_parser("convert_time", help="将所有srt文件的第一行字幕的开始时间改为00:00:00.000")
    subparser_subtitle_convert_time.add_argument("--path", required=True, help="包含srt文件夹的路径")
    subparser_subtitle_convert_time.set_defaults(func=executor.subtitleOperater.convert_time)

    #Command subtitle -> Subcommand count_srt_statistics
    subparser_subtitle_count_srt_statistics = subparser_subtitle.add_parser("count_srt_statistics", help="统计srt文件中的对话行数和英语词汇量")
    subparser_subtitle_count_srt_statistics.add_argument("--path", required=True, help="srt文件夹的路径")
    subparser_subtitle_count_srt_statistics.set_defaults(func=executor.subtitleOperater.count_srt_statistics)
    

    #Command picture
    parser_picture = subparsers.add_parser("picture", help="修改视频")
    subparser_picture = parser_picture.add_subparsers(dest="subcommand", help="picture命令的子命令")
    
    #Command picture -> Subcommand video_segment
    subparser_picture_video_segment = subparser_picture.add_parser("video_segment", help="根据多个srt文件的字幕时间将指定mp4切分为多个mp4片段")
    subparser_picture_video_segment.add_argument("--srt_path", required=True, help="保存srt文件的文件夹路径")
    subparser_picture_video_segment.add_argument("--video_path", required=True,help="MP4文件的路径")
    subparser_picture_video_segment.set_defaults(func=executor.pictureOperater.video_segment)
    
    # Command picture -> Subcommand cut_pc2phone
    subparser_picture_cut_pc2phone = subparser_picture.add_parser("cut_pc2phone", help="将pc尺寸的视频裁剪为手机大小的视频")
    subparser_picture_cut_pc2phone.add_argument("--path", required=False, help="视频文件夹的路径")
    subparser_picture_cut_pc2phone.set_defaults(func=executor.pictureOperater.cut_pc2phone)

    #Command picture -> Subcommand scale_pc2phone
    subparser_picture_scale_pc2phone = subparser_picture.add_parser("scale_pc2phone", help="将pc尺寸的视频缩放为手机大小的视频")
    subparser_picture_scale_pc2phone.add_argument("--path", required=False, help="视频文件夹的路径")
    subparser_picture_scale_pc2phone.set_defaults(func=executor.pictureOperater.scale_pc2phone)

    #Command picture -> Subcommand add_text
    subparser_picture_add_text = subparser_picture.add_parser("add_text", help="将pc尺寸的视频缩放为手机大小的视频")
    subparser_picture_add_text.add_argument("--path", required=False, help="视频文件夹的路径")
    subparser_picture_add_text.set_defaults(func=executor.pictureOperater.add_text)

    #Command picture -> Subcommand split_video
    subparser_picture_split_video = subparser_picture.add_parser("split_video", help="通过视频和字幕文件生成视频中每一句的朗读视频")
    subparser_picture_split_video.add_argument("--srt_path", required=True, help="字幕文件夹的路径")
    subparser_picture_split_video.add_argument("--video_path", required=True, help="视频文件夹的路径")
    subparser_picture_split_video.set_defaults(func=executor.pictureOperater.split_video)

    
    #Command picture -> Subcommand generate_images
    subparser_picture_generate_images = subparser_picture.add_parser("generate_images", help="生成几百张封面图片")
    subparser_picture_generate_images.add_argument("--path", required=True, help="视频的路径")
    subparser_picture_generate_images.set_defaults(func=executor.pictureOperater.generate_images)

    #Command ai
    parser_ai = subparsers.add_parser("ai", help="ai提问")
    subparser_ai = parser_ai.add_subparsers(dest="subcommand", help="ai命令的子命令")
    

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
    subparser_voice_youdao_voice.set_defaults(func=executor.voiceOperater.youdao_voice)

    # Command voice -> Subcommand gtts_voice
    subparser_voice_gtts_voice = subparser_voice.add_parser("gtts_voice", help="将文本转化为gtts发音")
    subparser_voice_gtts_voice.add_argument("--content", required=True, help="朗读内容")
    subparser_voice_gtts_voice.add_argument("--save_path", required=False, help="保存文件的路径")
    subparser_voice_gtts_voice.add_argument("--language", required=False, default="en" ,help="语言")
    subparser_voice_gtts_voice.add_argument("--slow", required=False, default=False ,help="慢速")
    subparser_voice_gtts_voice.set_defaults(func=executor.voiceOperater.gtts_voice)

    # Command voice -> Subcommand edge_tts_voice
    subparser_voice_edge_tts_voice = subparser_voice.add_parser("edge_tts_voice", help="将文本转化为edge_tts发音")
    subparser_voice_edge_tts_voice.add_argument("--content", required=True, help="朗读内容")
    subparser_voice_edge_tts_voice.add_argument("--save_path", required=False, help="保存文件的路径")
    subparser_voice_edge_tts_voice.add_argument("--language", required=False, default="en" ,help="语言")
    subparser_voice_edge_tts_voice.add_argument("--voice", required=False, default=None ,help="声音")
    subparser_voice_edge_tts_voice.set_defaults(func=executor.voiceOperater.edge_tts_voice)

    # Command voice -> Subcommand create_mp3_by_clone_voice
    subparser_voice_create_mp3_by_clone_voice = subparser_voice.add_parser("create_mp3_by_clone_voice", help="克隆声音创建新的声音")
    subparser_voice_create_mp3_by_clone_voice.add_argument("--content", required=True, help="朗读内容")
    subparser_voice_create_mp3_by_clone_voice.add_argument("--save_path", required=False, help="保存文件的路径")
    subparser_voice_create_mp3_by_clone_voice.add_argument("--language", required=False, default="en" ,help="语言")
    subparser_voice_create_mp3_by_clone_voice.set_defaults(func=executor.voiceOperater.create_mp3_by_clone_voice)
    

    # Command voice -> Subcommand clone_voice_conversion
    subparser_voice_clone_voice_conversion = subparser_voice.add_parser("clone_voice_conversion", help="转化wav音频为克隆声音")
    subparser_voice_clone_voice_conversion.add_argument("--target_wav", required=True, help="需要转化的wav文件路径")
    subparser_voice_clone_voice_conversion.add_argument("--save_path", required=False, help="保存文件的路径")
    subparser_voice_clone_voice_conversion.set_defaults(func=executor.voiceOperater.clone_voice_conversion)
    

    #Command merge
    parser_merge = subparsers.add_parser("merge", help="拼接")
    subparser_merge = parser_merge.add_subparsers(dest="subcommand", help="merge命令的子命令")

    # Command merge -> Subcommand merge1
    subparser_merge_merge1 = subparser_merge.add_parser("merge1", help="视频拼接1")
    subparser_merge_merge1.add_argument("--path", required=False, help="包含子文件夹的路径")
    subparser_merge_merge1.set_defaults(func=executor.mergeOperater.merge1)


    # Command merge -> Subcommand merge2
    subparser_merge_merge2 = subparser_merge.add_parser("merge2", help="相同编号的“1中英文对照 2跟读 3磨耳朵”视频拼接起来")
    subparser_merge_merge2.add_argument("--path", required=True, help="包含子文件夹的路径")
    subparser_merge_merge2.set_defaults(func=executor.mergeOperater.merge2)

    # Command merge -> Subcommand merge3
    subparser_merge_merge3 = subparser_merge.add_parser("merge3", help="将 所有“中英文对照”， 所有“跟读”， 所有“磨耳朵”视频拼接起来,形成三部完整的电影")
    subparser_merge_merge3.add_argument("--path", required=True, help="包含子文件夹的路径")
    subparser_merge_merge3.set_defaults(func=executor.mergeOperater.merge3)

    #Command custom
    parser_custom = subparsers.add_parser("custom", help="自定义命令")
    subparser_custom = parser_custom.add_subparsers(dest="subcommand", help="custom命令的子命令")

    # Command custom -> Subcommand custom1
    subparser_custom_custom1 = subparser_custom.add_parser("custom1", help="操作多个包含了有双语srt和视频的动画片的文件夹")
    subparser_custom_custom1.add_argument("--path", required=True, help="包含子文件夹的路径")
    subparser_custom_custom1.add_argument("--segment_second", required=False, help="间隔秒数分段依据")
    # 例如，使用 lambda 将 executor 传递给 custom1
    subparser_custom_custom1.set_defaults(func=lambda args: custom1(args, executor))


    #Command pdf
    parser_pdf = subparsers.add_parser("pdf", help="pdf操作")
    subparser_pdf = parser_pdf.add_subparsers(dest="subcommand", help="pdf命令的子命令")
    
    # Command pdf -> Subcommand pdf_to_txt_pdfplumber
    subparser_pdf_pdf_to_txt_pdfplumber = subparser_pdf.add_parser("pdf_to_txt_pdfplumber", help="pdf转txt")
    subparser_pdf_pdf_to_txt_pdfplumber.add_argument("--path", required=True, help="pdf文件或是包含了pdf文件的文件夹的路径")
    subparser_pdf_pdf_to_txt_pdfplumber.set_defaults(func=pdf_to_txt_pdfplumber)

    # Command pdf -> Subcommand split_sentences_2voice
    subparser_pdf_split_sentences_2voice = subparser_pdf.add_parser("split_sentences_2voice", help="txt转mp3")
    subparser_pdf_split_sentences_2voice.add_argument("--path", required=True, help="txt文件或是包含了txt文件的文件夹的路径")
    subparser_pdf_split_sentences_2voice.set_defaults(func=split_sentences_2voice)

    


    # and more ...

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
