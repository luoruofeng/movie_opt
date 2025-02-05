import os
import subprocess
import traceback
import chardet  # 用于自动检测文件编码
import re
from PIL import Image, ImageDraw, ImageFont
from movie_opt.utils import *
import shutil
from datetime import timedelta
from movie_opt.commands.ai import get_phrase,get_hard_words,ask_english_teacher_local_llm
from movie_opt.qwen_utils import QwenPlusAssistant
import ass
import srt
import re
from datetime import timedelta

def count_srt_statistics(args):
    """
    统计 SRT 文件的字幕行数和唯一英文单词的数量。

    :param srt_file_path: 字幕文件的路径
    :return: 一个元组 (字幕行数, 唯一英文单词数量)
    """
    subtitle_line_count = 0
    unique_words = set()
    srt_file_path = args.path
    if not os.path.exists(srt_file_path):
        logging.info(f"统计英文单词的数量失败,没有srt文件:{srt}")
        return 0,0
    try:
        with open(srt_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            # 去掉时间戳、序号等非字幕内容
            if re.match(r'^\d+$', line.strip()) or re.match(r'-->+', line.strip()):
                continue

            # 非空行即为字幕内容
            stripped_line = line.strip()
            if stripped_line:
                subtitle_line_count += 1

                # 提取字幕中的英文单词（不区分大小写）
                words = re.findall(r'[a-zA-Z]+', stripped_line)
                unique_words.update(word.lower() for word in words)

        return subtitle_line_count, len(unique_words)

    except FileNotFoundError:
        print(f"File not found: {srt_file_path}")
        return 0, 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0, 0


# 全局变量，定义 ASS 文件的样式
ASS_STYLE = """
[Script Info]
Title: Converted SRT to ASS
Original Script: Python Script
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Chinese,Alibaba Sans Bold,27,&H00FFFFFF,&H00000000,&H00000000,&H00FFFFFF,1,0,0,0,100,100,0,0,3,4,0,2,10,10,10,1
Style: English,AlibabaSans-HeavyItalic,31,&H00FFFFFF,&H00000000,&H00000000,&H00FFFFFF,1,0,0,0,100,100,-2,0,1,4,0,2,10,10,10,1
Style: Chinese_yellow,Alibaba Sans Bold,27,&H00FFFF00,&H00000000,&H00000000,&H00FFFF00,1,0,0,0,100,100,0,0,3,4,0,2,10,10,10,1
Style: English_yellow,AlibabaSans-HeavyItalic,37,&H00FFFF00,&H00000000,&H00000000,&H00FFFF00,1,0,0,0,100,100,-2,0,1,4,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


from movie_opt.commands.ai import init_ai
def change_ass_hard_word_style(args):
    file_path = args.path
    if not os.path.exists(file_path):
        logging.info(f"change_ass_hard_word_style 文件不存在:{file_path}")
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    dialogue_lines = []

    init_ai()
    
    for line in lines:
        if line.startswith("Dialogue:"):
            dialogue_lines.append(line)
        else:
            new_lines.append(line)
    
    modified_dialogues = []
    
    for i in range(0, len(dialogue_lines) - 1, 2):
        ch_line = dialogue_lines[i]
        en_line = dialogue_lines[i + 1]
        
        # 检查是否是中英文配对
        if 'Chinese' in ch_line and 'English' in en_line:
            ch_text = ch_line.split(',', 9)[-1].strip()
            en_text = en_line.split(',', 9)[-1].strip()
            
            print(f"Chinese: {ch_text}")
            print(f"English: {en_text}")

            try:
                hard_words = get_hard_words(ch_text, en_text)
                if hard_words is not None and len(hard_words) > 0:
                    for hard_word in hard_words:
                        most_hard_word,translation,phonetic,match_cn_txt = hard_word
                        # 替换match_cn_txt为黄色字体
                        if match_cn_txt is not None and match_cn_txt in ch_text:
                            replacement = r'{\\c&H00FFFF00&}'+match_cn_txt+r'{\\r}'
                            ch_line = re.sub(match_cn_txt, replacement, ch_line, flags=re.IGNORECASE)


                        # 替换most_hard_word为黄色字体并且改字体大小
                        if re.search(rf'\b{most_hard_word}\b', en_text, re.IGNORECASE):
                            replacement = r'{\\c&H00FFFF00&\\fs37}'+most_hard_word+r'{\\r}'
                            en_line = re.sub(most_hard_word, replacement, en_line, flags=re.IGNORECASE)

                    print(f"Chinese: {ch_line} English: {en_line}")
            except Exception as e:
                print(f"An error occurred: {e}")
                logging.error(f"查询最难单词出错 ch:{ch_text} en:{en_text} e:{e}")
                traceback.print_exc()
                print(f"查询最难单词出错 ch:{ch_text} en:{en_text} e:{e}")

                
            modified_dialogues.append(ch_line)
            modified_dialogues.append(en_line)
        else:
            modified_dialogues.append(ch_line)
            modified_dialogues.append(en_line)
    
    # 重新组合文件内容
    new_lines.extend(modified_dialogues)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("字幕文件处理完成并已保存！")


def detect_encoding(file_path):
    """检测文件的编码"""
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read())
        return result.get("encoding", "utf-8")

def split_text(text):
    """分离中文和英文"""
    import re
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", text))
    english = " ".join(re.findall(r"[a-zA-Z0-9,.'!? ]+", text))
    return chinese.strip(), english.strip()

def subtitle_srt_to_ass(srt_file, ass_file):
    """将 SRT 文件转换为 ASS 文件"""
    # 自动检测编码
    encoding = detect_encoding(srt_file)
    print(f"检测到 {srt_file} 的编码为: {encoding}")

    try:
        with open(srt_file, "r", encoding=encoding) as srt, open(ass_file, "w", encoding="utf-8") as ass:
            # 写入 ASS 样式
            ass.write(ASS_STYLE)
            ass.write("\n")

            # 转换内容
            buffer = []  # 用于存储当前字幕块的内容
            for line in srt:
                stripped_line = line.strip()
                if stripped_line.isdigit():  # 检测到字幕序号
                    if buffer:  # 如果有未处理的字幕块，先处理它
                        process_buffer(buffer, ass)
                    buffer = []  # 重置缓冲区
                elif "-->" in stripped_line:  # 检测到时间轴
                    buffer.append(stripped_line)  # 时间轴放入缓冲区
                elif stripped_line:  # 检测到字幕内容
                    buffer.append(stripped_line)  # 字幕内容放入缓冲区

            # 处理最后一块字幕
            if buffer:
                process_buffer(buffer, ass)
    except UnicodeDecodeError as e:
        print(f"文件 {srt_file} 编码错误: {e}")
        print("请手动检查文件编码或使用其他工具转换编码。")

def process_buffer(buffer, ass):
    """处理字幕缓冲区，将其写入 ASS 文件"""
    if len(buffer) < 2:
        return  # 不完整的字幕块，跳过处理

    time_line = buffer[0]
    text = " ".join(buffer[1:]).replace("\n", " ")  # 合并多行字幕内容为一行
    start, end = time_line.split(" --> ")
    start = format_time(start.strip().replace(",", "."))
    end = format_time(end.strip().replace(",", "."))
    
    chinese, english = split_text(text)
    if chinese:
        ass.write(f"Dialogue: 0,{start},{end},Chinese,,0,0,0,,{chinese}\n")
    if english:
        ass.write(f"Dialogue: 0,{start},{end},English,,0,0,0,,{english}\n")

def format_time(time_str):
    """格式化时间字符串，确保小数点后只保留两位"""
    return re.sub(r"(\.\d{2})\d*", r"\1", time_str)

def srt2ass(args):
    print(f"SRT 文件夹路径: {args.path}")

    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return

    # 遍历目录中的所有 SRT 文件
    for file_name in os.listdir(path):
        if file_name.endswith(".srt"):
            srt_file = os.path.join(path, file_name)
            ass_file = os.path.splitext(srt_file)[0] + ".ass"
            format_translation_srt(srt_file)

            print(f"转换文件: {srt_file} -> {ass_file}")
            subtitle_srt_to_ass(srt_file, ass_file)

    print("转换完成！")



def addass(args):
    print(f"SRT 文件夹路径: {args.path}")

    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return

    # 遍历目录中的所有 ASS 文件和视频文件
    ass_files = [os.path.join(path, file)
                 for file in os.listdir(path) if file.endswith(".ass")]
    video_files = [os.path.join(path, file)
                   for file in os.listdir(path)
                   if file.endswith((".mp4", ".mkv", ".avi", ".mov"))]

    if len(ass_files) == 0:
        print("没有找到字幕文件")
    if len(video_files) == 0:
        print("没有找到视频文件")

    ass_path = ass_files[0]
    video_path = video_files[0]
    video_name = os.path.basename(video_path)

    # 获取原视频文件的扩展名
    video_extension = os.path.splitext(video_path)[1]
    output_path = os.path.join(path, f"subtitle_{video_name}")

    # 将路径标准化为相对路径
    relative_ass_path = os.path.relpath(ass_path, start=path)
    relative_video_path = os.path.relpath(video_path, start=path)
    relative_output_path = os.path.relpath(output_path, start=path)
    
    command = [
        'ffmpeg',
        '-i', relative_video_path,         # 输入视频文件
        '-vf', f"ass={relative_ass_path}",  # 应用字幕滤镜
        '-c:v', 'libx264',                 # 对视频流重新编码
        '-preset', 'ultrafast',             # 快速编码
        '-map', '0:v:0',                   # 只保留第一个视频流 (Stream #0:0)
        '-map', '0:a:0',                   # 只保留第一个音频流 (Stream #0:1，英语)
        '-c:a', 'aac',                     # 使用AAC编码器重新编码音频
        '-b:a', '192k',                    # 设置音频比特率 (例如 192k)
        '-ac', '2',                        # 设置输出音频为立体声（可选，根据需要调整）
        '-map_metadata', '-1',             # 清除全局元信息
        '-movflags', 'use_metadata_tags',  # 确保写入新的元信息
        relative_output_path             # 输出文件路径
    ]

    try:
        subprocess.run(command, check=True, cwd=path)  # 指定 cwd 为 path，确保相对路径正确
        print(f"已为视频 {video_name} 添加字幕，保存为 {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"添加字幕失败: {e}")



def detect_encoding(file_path):
    """检测文件的编码"""
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read())
        return result.get("encoding", "utf-8")


def write_srt_file(file_path, blocks):
    """将字幕块写入新的 SRT 文件"""
    with open(file_path, "w", encoding="utf-8") as file:
        for idx, block in enumerate(blocks):
            file.write(f"{idx + 1}\n")
            for line in block:
                file.write(line + "\n")
            file.write("\n")

def is_time_equal(block1, block2):
    """检查两个字幕块的时间戳是否相同"""
    time1 = block1[1]
    time2 = block2[1]
    return time1 == time2


def sequencesrt(args):
    print(f"SRT 文件夹路径: {args.path}")

    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return

    # 获取所有 SRT 文件
    srt_files = [f for f in os.listdir(path) if f.endswith(".srt")]

    for file in srt_files:
        srt_path = os.path.join(path, file)
        new_srt_lines = []
        single_line_only = True

        with open(srt_path, "r", encoding="utf-8") as srt_file:
            content = srt_file.readlines()

        # 解析 SRT 内容
        subtitles = []
        temp_block = []
        for line in content:
            line = line.strip()
            if line:
                temp_block.append(line)
            else:
                if temp_block:
                    subtitles.append(temp_block)
                temp_block = []

        if temp_block:
            subtitles.append(temp_block)

        # 检查和修改字幕
        for i in range(len(subtitles)):
            block = subtitles[i]
            if len(block) < 3:
                continue  # 略过不完整的块

            subtitle_lines = block[2:]  # 实际字幕行
            if len(subtitle_lines) > 1:
                single_line_only = False
                # 如果显示两行字幕，将其合并并调整时间
                start_time, end_time = block[1].split(" --> ")
                if i + 1 < len(subtitles):
                    next_start_time = subtitles[i + 1][1].split(" --> ")[0]
                    block[1] = f"{start_time} --> {next_start_time}"

                # 合并所有字幕行
                combined_text = " ".join(subtitle_lines)
                new_srt_lines.append(block[:2] + [combined_text])
            else:
                new_srt_lines.append(block)

        # 如果所有字幕都只有一行，则跳过处理
        if single_line_only:
            print(f"文件 {file} 已符合条件，无需处理。")
            continue

        # 保存修改后的字幕到新文件，并删除原始文件
        new_srt_path = os.path.join(path, f"modified_{file}")
        with open(new_srt_path, "w", encoding="utf-8") as new_srt_file:
            for block in new_srt_lines:
                new_srt_file.write("\n".join(block) + "\n\n")

        os.remove(srt_path)
        print(f"已处理文件: {file}, 新文件保存为: modified_{file}")


colors_ex = {"tell": "red", "about": "blue","告诉":"yellow","我的家":"blue"}

def extract_text_from_srt(file_path,split_symbol=",\n"):
    """
    从 SRT 文件提取纯文本内容，去除编号、时间戳和空行。
    
    :param file_path: SRT 文件路径
    :return: 提取的文本内容（字符串）
    """
    with open(file_path, 'r', encoding='utf-8') as srt_file:
        content = srt_file.read()
        print(content)
        # 逐行处理 SRT 文件
        lines = content.splitlines()
        txt = []
        for line in lines:
            # 跳过编号、时间戳和空行
            if re.match(r'^\d+$', line) or re.match(r'\d{2}:\d{2}:\d{2},\d{3}', line) or line.strip() == '':
                continue
            txt.append(line.strip())
        
        return split_symbol.join(txt)
    return None

def srt2txtpng(args):
    print(f"SRT 文件夹路径: {args.path}")

    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return

    # 遍历目录中的所有 SRT 文件
    for file_name in os.listdir(path):
        if file_name.endswith(".srt"):
            file_path = os.path.join(path, file_name)
            
            # 调用新封装的方法提取文本
            txt = extract_text_from_srt(file_path)
            
            # 生成 PNG 保存路径
            output_png_path = os.path.join(path, os.path.splitext(file_name)[0] + ".png")
            
            # 创建 PNG
            create_png_with_text(txt, output_png_path)
            print(f"处理完成：{output_png_path}")    

from PIL import Image

# 提高 Pillow 允许的最大像素数
Image.MAX_IMAGE_PIXELS = None
def create_png_with_text(text, output_path):
    # 图片的宽度（固定）
    image_width = 1284
    
    # 设置字体和大小
    font_path = "C:\\Users\\luoruofeng\\AppData\\Local\\Microsoft\\Windows\\Fonts\\AlibabaPuHuiTi-3-75-SemiBold.ttf"  # 根据系统字体路径修改
    font_size = 44
    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        print("找不到字体文件，请修改路径或安装字体。")
        return

    # 创建一个临时画布
    dummy_image = Image.new('RGB', (image_width, 1), "white")
    draw = ImageDraw.Draw(dummy_image)

    # 自动换行处理文本
    margin = 10
    line_spacing = 1  # 行间距
    wrapped_text = wrap_text(text, draw, font, image_width - 2 * margin)

    # 计算文字总高度
    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=line_spacing)
    text_height = bbox[3] - bbox[1]
    image_height = text_height + 2 * margin

    # 创建实际的图片
    image = Image.new('RGB', (image_width, image_height), "white")
    draw = ImageDraw.Draw(image)

    # 绘制文本
    lines = wrapped_text.split("\n")
    y = margin
    for li, line in enumerate(lines):
        if line.strip() == "":
            continue
        x = margin
        kw_index: list[tuple[int, str]] =  find_keywords_indices(line=line,key_words=colors_ex.keys())
        for ci, char in enumerate(line):  # 按字符遍历
            bbox = draw.textbbox((x, y), char, font=font)
            includ_kw = False
            if kw_index != None and len(kw_index) > 0:
                for si,kw in kw_index:
                    start = si
                    end = si + len(kw)
                    if ci >= start and ci < end:
                        if ci == start:
                            # 绘制带背景的字符
                            bg_bbox = draw.textbbox((x, y), kw, font=font)
                            draw.rectangle(bg_bbox, fill="lightgreen")  # 背景色
                        draw.text((x, y), char, fill=colors_ex[kw], font=font)
                        includ_kw = True
                if not includ_kw:
                    # 普通字符绘制
                    draw.text((x, y), char, fill="black", font=font)
            else:
                # 普通字符绘制
                draw.text((x, y), char, fill="black", font=font)

            # 更新 x 坐标
            char_width = bbox[2] - bbox[0]
            x += char_width

        # 更新 y 坐标，用于下一行
        text_height = font.getbbox(line)[3] - font.getbbox(line)[1]
        y += text_height + line_spacing


    # 保存图片
    image.save(output_path, "PNG")
    crop_image(image_path=output_path,height=y+5)
    print(f"PNG 图片已保存: {output_path}")

def wrap_text(text, draw, font, max_width):
    """根据最大宽度自动换行文本"""
    lines = []
    for paragraph in text.split("\n"):
        current_line = ""
        for word in paragraph.split():
            # 测试当前行加上新单词后的宽度
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]  # 宽度计算
            if width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
    return "\n".join(lines)




def parse_srt_time(timestamp):
    """ 将 SRT 时间戳解析为秒和毫秒 """
    # 使用正则表达式分割时间戳，匹配到可能有小时、分钟、秒和毫秒的格式
    match = re.match(r"(\d+):(\d+):(\d+),(\d+)", timestamp)
    if not match:
        raise ValueError("Invalid SRT timestamp format")
    
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds, milliseconds


def write_srt_file(output_folder, original_name, index, segments):
    """ 将分段后的内容写入新的 SRT 文件 """
    file_name = f"{original_name}-{index}.srt"
    output_path = os.path.join(output_folder, file_name)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(segments))
    print(f"写入文件: {output_path}")
    format_translation_srt(output_path) # 格式化




def process_srt_segment_file(srt_path, output_folder, segment_second):
    """ 处理单个 SRT 文件，将其分段 """
    print(f"正在处理文件: {srt_path}")
    original_name = os.path.splitext(os.path.basename(srt_path))[0]
    with open(srt_path, "r", encoding="utf-8") as file:
        lines = file.read().split("\n")

    current_segment = []
    previous_end_time = 0  # 上一句结束时间
    segment_index = 1  # 文件序号

    time_pattern = r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}"
    for line in lines:
        if not line.strip():  # 跳过空行
            continue

        if bool(re.search(time_pattern, line)):  # 匹配时间戳
            # parts = line.split("\n", 2)  # 分成序号、时间戳、字幕文本
            # if len(parts) < 2:
            #     continue


            # 解析时间戳
            time_range = line.strip()
            start_time, end_time = time_range.split("-->")
            
            start_time_sec = parse_srt_time(start_time.strip())[0]
            end_time_sec = parse_srt_time(end_time.strip())[0]

            # 判断是否需要分段
            if previous_end_time and (start_time_sec - previous_end_time > int(segment_second)):
                last_line = None
                if current_segment is not None:
                    last_line = current_segment[-1]
                    del(current_segment[-1])

                # 保存当前分段
                write_srt_file(output_folder, original_name, segment_index, current_segment)

                segment_index += 1
                current_segment = []  # 清空当前分段内容
                current_segment.append(last_line)

            # 添加当前行到分段中
            current_segment.append(line)
            previous_end_time_temp = end_time
            previous_end_time = end_time_sec  # 更新上一句的结束时间
        else:
            current_segment.append(line)

    # 保存最后一个分段
    if current_segment:
        print( current_segment)
        write_srt_file(output_folder, original_name, segment_index, current_segment)


        
def srtsegment(args): 
    print(f"SRT 文件或文件夹路径: {args.path}")

    segment_second = args.second  # 间隔分段秒数

    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return



    # 创建新的 srt分段 文件夹
    def create_srt_seg_dir(path):
        output_folder = os.path.join(path, "srt分段")
        if os.path.exists(output_folder):
            print(f"已存在 srt分段 文件夹: {output_folder}")
            shutil.rmtree(output_folder)  # 删除旧的分段文件夹
        print(f"创建 srt分段 文件夹: {output_folder}")
        os.makedirs(output_folder)
        return output_folder

    # 判断路径是文件还是文件夹
    if os.path.isfile(path) and path.endswith(".srt"):
        output_folder = create_srt_seg_dir(os.path.dirname(path))
        # 如果是单个 SRT 文件
        process_srt_segment_file(path, output_folder, segment_second)
    elif os.path.isdir(path):
        output_folder = create_srt_seg_dir(path)
        # 如果是文件夹，遍历所有 SRT 文件
        for file_name in os.listdir(path):
            if file_name.endswith(".srt"):
                file_path = os.path.join(path, file_name)
                process_srt_segment_file(file_path, output_folder, segment_second)
    else:
        print("提供的路径不是 SRT 文件或文件夹！")
        return

    print(f"处理完成，分段文件保存在: {output_folder}")




def convert_srt_to_timedelta (srt_time):
    """解析 SRT 时间戳，兼容不同长度"""
    try:
        # 匹配小时、分钟、秒和可选的毫秒部分
        match = re.match(r"(\d+):(\d+):(\d+),(\d+)", srt_time)
        if match:
            hours, minutes, seconds, milliseconds = match.groups()
            # 如果有毫秒部分，则将毫秒转换为秒并加到秒上
            seconds = float(seconds) + float(milliseconds or 0) / 1000
            return timedelta(hours=float(hours), minutes=float(minutes), seconds=seconds)
        else:
            raise ValueError("Invalid SRT time format")
    except ValueError as e:
        print(f"Error parsing SRT time: {e}")
        return None

def format_srt_time(delta):
    """格式化时间为 SRT 时间戳"""
    total_seconds = int(delta.total_seconds())
    milliseconds = int(delta.microseconds / 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def adjust_srt_file(file_path):
    """调整 SRT 文件的时间"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    adjusted_lines = []
    first_start_time = None
    previous_end_time = None

    for line in lines:
        time_match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", line)
        if time_match:
            start_time = convert_srt_to_timedelta(time_match.group(1))
            end_time = convert_srt_to_timedelta(time_match.group(2))

            if first_start_time is None:
                shift = start_time  # The initial shift is the start time of the first subtitle
                first_start_time = start_time

            new_start_time = start_time - shift
            new_end_time = end_time - shift

            if previous_end_time is not None:
                gap = new_start_time - previous_end_time
                if gap < timedelta(0):
                    gap = timedelta(0)  # Ensure no negative time gap
                new_start_time = previous_end_time + gap
                new_end_time = new_start_time + (end_time - start_time)

            previous_end_time = new_end_time

            adjusted_lines.append(f"{format_srt_time(new_start_time)} --> {format_srt_time(new_end_time)}\n")
        else:
            adjusted_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(adjusted_lines)

def convert_time(args):
    print(f"SRT 文件夹路径: {args.path}")

    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return
    
    def process_srt(file_path):
        """
        对单个 .srt 文件进行操作的核心逻辑。
        :param file_path: .srt 文件路径
        """
        print(f"Processing: {file_path}")
        print(f"正在处理文件: {file_name}")
        adjust_srt_file(file_path)
        print(f"已完成文件: {file_name}")

    if os.path.isdir(path):
        # 遍历目录中的所有 SRT 文件
        for file_name in os.listdir(path):
            if file_name.endswith(".srt"):
                process_srt(os.path.join(path, file_name))
    elif os.path.isfile(path) and path.lower().endswith('.srt'):
        # 如果是单个 .srt 文件路径
        process_srt(path)
    else:
        print("输入的路径无效或不包含 .srt 文件！")



from enum import Enum
class PUNCTUATION_MARK(Enum):
    SEQUENCE = 1
    TIME_STAMP = 2
    CONTENT = 3
    

# 重新排版srt文件
def reposition_srt(args):
    # 检查 args.path 是否存在且是否是文件夹
    if not os.path.exists(args.path):
        print(f"路径 {args.path} 不存在。")
        return

    srt = args.path
    convert_to_utf8(srt)
    txt = extract_text_from_srt(srt) # 提取srt中的文本内容
    txt = txt.replace("\n","")
    txt = remove_brackets_content(txt,holder_token=" ")

    print(f" srt文件内容:{txt}")
    remove_non_alphanumeric_txt =  remove_non_alphanumeric(txt)

    # 重新划分文本内容的标点符号
    sentences = None
    for i in range(4):
        print(f"第{i+1}次本地模型尝试")
        reply = ask_english_teacher_local_llm("不增加任何单词，不减少任何单词以及不改变任何单词顺序的情况下，语法和单词错误也不改变任何单词以及单词顺序的情况下，删除这段话中错误的标点符号，添加正确的标点符号，直接回答，不要回复任何无效内容，不要回复任何描述语言："+txt,model_name="qwen2.5:14b")
        reply = reply.replace("\n","")
        if remove_non_alphanumeric(reply) != remove_non_alphanumeric_txt:
            print(f"reply:{reply}")
            print(f"第{i+1}次本地模型尝试失败 字符数:{len(remove_non_alphanumeric(reply))} 正确字符数:{len(remove_non_alphanumeric_txt)}")
            continue
        else:
            sentences = split_sentences(reply)
            break
    
    if sentences is None:
        QWEN_ASSISTANT = QwenPlusAssistant( model='qwen-max')
        for i in range(3):
            print(f"第{i+1}次远程模型尝试")
            qwen_assistant = QWEN_ASSISTANT.converse("不增加任何单词，不减少任何单词以及不改变任何单词顺序的情况下，语法和单词错误也不改变任何单词以及单词顺序的情况下，删除这段话中错误的标点符号，添加正确的标点符号，直接回答，不要回复任何无效内容，不要回复任何描述语言："+txt)
            reply = reply.replace("\n","")
            if remove_non_alphanumeric(reply) == remove_non_alphanumeric_txt:
                sentences = split_sentences(reply)
                break
            else:
                print(f"reply:{reply}")
                print(f"第{i+1}次远程模型尝试失败 字符数:{len(remove_non_alphanumeric(reply))} 正确字符数:{len(remove_non_alphanumeric_txt)}")
                continue
        
    if sentences is None:
        raise Exception("重新划分文本内容的标点符号失败,无法使用大模型重新划分文本内容的标点符号")
    
    # 定义匹配 SRT 时间戳的正则表达式
    time_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')
    sentence_index = 0
    character_count = 0
    result = []
    # 遍历 SRT 文件中的每一行
    with open(srt, 'r', encoding='utf-8') as file:
        while True:
            previous_line_type = None
            st,et = None,None
            cc = None
            cline_number = None
            cst, cet = None,None
            for line_number, line in enumerate(file, start=1):
                stripped_line = line.strip()
                stripped_line = stripped_line.replace("\n","")

                if not stripped_line:
                    print(f"第 {line_number} 行: 空行")
                elif stripped_line.isdigit(): # 序号
                    print(f"第 {line_number} 行: 序号 ({stripped_line})")
                    previous_line_type = PUNCTUATION_MARK.SEQUENCE
                elif time_pattern.match(stripped_line): # 时间戳
                    time_match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", stripped_line)
                    if time_match:
                        cst,cet = time_match.groups()
                        previous_line_type = PUNCTUATION_MARK.TIME_STAMP
                        
                else: # 内容
                    s = sentences[sentence_index]
                    if stripped_line in s:
                        cc += stripped_line
                        remove_punctuation_s = remove_non_alphanumeric(s)
                        remove_punctuation_stripped_line = remove_non_alphanumeric(stripped_line)
                        len_remove_punctuation_s = len(remove_punctuation_s)
                        len_remove_punctuation_stripped_line = len(remove_punctuation_stripped_line)
                        character_count += len_remove_punctuation_stripped_line
                        print(f"第 {line_number} 行: 内容 ({stripped_line}) remove_punctuation_s: {remove_punctuation_s} remove_punctuation_stripped_line: {remove_punctuation_stripped_line} len_remove_punctuation_s: {len_remove_punctuation_s} len_remove_punctuation_stripped_line: {len_remove_punctuation_stripped_line} character_count: {character_count}")
                        
                        if str.startswith(remove_punctuation_s, remove_punctuation_stripped_line):
                            st = cst
                            print(f"设置st: {st}")
                        if str.endswith(remove_punctuation_s, remove_punctuation_stripped_line) and character_count >= len_remove_punctuation_s:
                            et = cet
                            print(f"设置et: {et}")
                            item = [str(sentence_index),st+" --> "+et,cc]
                            result.append(item)
                            sentence_index += 1
                            character_count = 0
                    previous_line_type = PUNCTUATION_MARK.CONTENT
    print(f"result: {result}")
    # 将结果写入文件
    with open(srt, 'w', encoding='utf-8') as file:
        for sublist in result:
            print(f"写入文件: {srt}")
            file.write("\n".join(map(str, sublist)) + "\n\n")
    return result


#合并中英文srt文件
def mergesrt(args):
    print(f"SRT 文件夹路径: {args.path}")

    # 如果路径为空，则使用当前目录
    path = args.path if args.path else os.getcwd()

    # 检查路径是否存在
    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return

    # 获取所有 SRT 文件
    srt_files = [f for f in os.listdir(path) if f.endswith(".srt")]
    
    if len(srt_files) < 2:
        print("没有找到两个以上的SRT文件")
        return
    
    if len(srt_files) > 2:
        print("没有找到两个以上的SRT文件")
        return
    
    f1 = srt_files[0]
    f2 = srt_files[1]
    previous_line_type = None
    match_timestamp = False
    f2_read_cursor = 0
    time_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')
    
    result = []
    with open(os.path.join(path, f1), "r", encoding="utf-8") as f1_file, open(os.path.join(path, f2), "r", encoding="utf-8") as f2_file:
        f1_content = f1_file.readlines()
        f2_content = f2_file.readlines()


        for line in f1_content:
            stripped_line = line.strip()

            if not stripped_line:
                result.append("\n") # 空
            elif stripped_line.isdigit(): # 序号
                result.append(stripped_line)
                previous_line_type = PUNCTUATION_MARK.SEQUENCE
            elif time_pattern.match(stripped_line): # 时间戳
                time_match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", stripped_line)
                if time_match:
                    cst,cet = time_match.groups()
                    result.append(stripped_line)
                    for f2_line in f2_content[f2_read_cursor:]:
                        f2_stripped_line = f2_line.strip()
                        if not f2_stripped_line:
                            pass # 空
                        elif time_pattern.match(stripped_line):
                            time_match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", stripped_line)
                            if time_match:
                                st2,et2 = time_match.groups()
                                st2f = timestamp_convert_to_seconds(st2)
                                et2f = timestamp_convert_to_seconds(et2)
                                cstf = timestamp_convert_to_seconds(cst)
                                cetf = timestamp_convert_to_seconds(cet)
                                if (st2f > cstf and et2f > cetf):
                                    match_timestamp = False
                                    break
                                elif st2f == cstf and et2f == cetf:
                                    f2_read_cursor += 1
                                    match_timestamp = True
                                    break
                                else:
                                    match_timestamp = False
                                    f2_read_cursor += 1
                                    continue
                            else:
                                f2_read_cursor += 1
                                continue
                        else:
                            f2_read_cursor += 1
                            continue

                    previous_line_type = PUNCTUATION_MARK.TIME_STAMP
                    
            else: # 内容
                result.append(stripped_line)
                if match_timestamp:
                    if previous_line_type == PUNCTUATION_MARK.CONTENT:
                        f2_read_cursor+=1
                        result.append(f2_content[f2_read_cursor]+"\n")
                    else:
                        result.append(f2_content[f2_read_cursor]+"\n")
                previous_line_type = PUNCTUATION_MARK.CONTENT
    print(f"合并后的结果: {result}")
    # 将结果写入文件
    with open(os.path.join(path, f1), "w", encoding="utf-8") as f1_file:
        f1_file.write("\n".join(result))
    # 删除 f2 文件
    os.remove(os.path.join(path, f2))
    print("合并完成！")



def convert_ass_to_srt(args):
    """
    将给定的 ASS 字幕文件转换为同名的 SRT 字幕文件，并保存。
    :param ass_file_path: str, ASS 字幕文件的路径
    """
    ass_file_path = args.path
    srt_file_path = ass_file_path.rsplit('.', 1)[0] + ".srt"
    
    with open(ass_file_path, encoding="utf-8-sig") as f:
        doc = ass.parse(f)
    
    subtitles = []
    for index, event in enumerate(doc.events, start=1):
        start = timedelta(seconds=event.start.total_seconds())
        end = timedelta(seconds=event.end.total_seconds())
        text = re.sub(r"\{\\.*?\}", "", event.text)  # 使用正则删除大括号及其内容
        text = text.replace("\\N", "\n")  # 处理换行符
        
        subtitles.append(srt.Subtitle(index, start, end, text))
    
    with open(srt_file_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))
    
    print(f"转换完成: {srt_file_path}")


