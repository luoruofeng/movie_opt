import os
import chardet  # 用于自动检测文件编码
import subprocess
import chardet  # 用于自动检测文件编码
import re
import json
from PIL import Image, ImageDraw, ImageFont
from movie_opt.utils import *


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
Style: Chinese,SimSun,10,&H00FFFFFF,&H0000FFFF,&H00000000,&H99808080,0,0,0,0,100,100,0,0,3,1,0,7,10,10,10,1
Style: English,Arial,16,&H00FFFF00,&H0000FFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,1,0,7,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

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
    ass_files = {os.path.splitext(file)[0]: os.path.join(path, file)
                 for file in os.listdir(path) if file.endswith(".ass")}
    video_files = {os.path.splitext(file)[0]: os.path.join(path, file)
                   for file in os.listdir(path)
                   if file.endswith((".mp4", ".mkv", ".avi", ".mov"))}

    # 为每个视频文件添加对应的字幕
    for video_name, video_path in video_files.items():
        if video_name in ass_files:
            ass_path = ass_files[video_name]
            
            # 获取原视频文件的扩展名
            video_extension = os.path.splitext(video_path)[1]
            output_path = os.path.join(path, f"{video_name}_subtitled{video_extension}")

            # 将路径标准化为相对路径
            relative_ass_path = os.path.relpath(ass_path, start=path)
            relative_video_path = os.path.relpath(video_path, start=path)
            relative_output_path = os.path.relpath(output_path, start=path)
            
            # 使用 ffmpeg 添加字幕
            command = [
                'ffmpeg', '-i', relative_video_path, '-vf', f"ass={relative_ass_path}",
                '-c:a', 'copy', relative_output_path
            ]
            try:
                subprocess.run(command, check=True, cwd=path)  # 指定 cwd 为 path，确保相对路径正确
                print(f"已为视频 {video_name} 添加字幕，保存为 {output_path}")
            except subprocess.CalledProcessError as e:
                print(f"添加字幕失败: {e}")
        else:
            print(f"未找到与视频 {video_name} 对应的 ASS 文件，跳过处理")




def detect_encoding(file_path):
    """检测文件的编码"""
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read())
        return result.get("encoding", "utf-8")

def read_srt_file(file_path):
    """读取 SRT 文件内容并按字幕块返回"""
    encoding = detect_encoding(file_path)
    with open(file_path, "r", encoding=encoding) as file:
        content = file.read()
    blocks = []
    current_block = []

    for line in content.splitlines():
        if line.strip() == "":
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    
    if current_block:  # 如果最后一个块未添加
        blocks.append(current_block)
    
    return blocks

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
    merged_files = set()

    for i, file1 in enumerate(srt_files):
        if file1 in merged_files:
            continue
        
        for file2 in srt_files[i+1:]:
            if file2 in merged_files:
                continue
            
            file1_path = os.path.join(path, file1)
            file2_path = os.path.join(path, file2)

            # 读取两个文件内容
            blocks1 = read_srt_file(file1_path)
            blocks2 = read_srt_file(file2_path)

            # 检查时间戳数量和对应的时间是否相同
            if len(blocks1) == len(blocks2) and all(is_time_equal(b1, b2) for b1, b2 in zip(blocks1, blocks2)):
                merged_blocks = []

                for b1, b2 in zip(blocks1, blocks2):
                    # 合并内容
                    time_line = b1[1]  # 时间戳行
                    merged_content = b2[2:] + b1[2:]  # 英文在上，中文在下
                    merged_blocks.append([time_line] + merged_content)

                # 保存新文件
                merged_file_name = os.path.splitext(file1)[0] + "_merged.srt"
                merged_file_path = os.path.join(path, merged_file_name)
                write_srt_file(merged_file_path, merged_blocks)

                # 标记为已处理并删除原文件
                merged_files.add(file1)
                merged_files.add(file2)
                os.remove(file1_path)
                os.remove(file2_path)

                print(f"合并并删除: {file1} 和 {file2} -> {merged_file_name}")
                break
    print("合并完成！")



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
            
            # 提取 SRT 文件中的字幕内容
            with open(file_path, 'r', encoding='utf-8') as srt_file:
                content = srt_file.read()
            
            # 去掉编号、时间和空行，只保留字幕内容
            lines = content.splitlines()
            txt = []
            for line in lines:
                # 匹配时间格式：00:00:00,000 --> 00:00:00,000 或者编号
                if re.match(r'^\d+$', line) or re.match(r'\d{2}:\d{2}:\d{2},\d{3}', line) or line.strip() == '':
                    continue
                txt.append(line.strip())
            txt = "\n".join(txt)
            
            # 生成 PNG 保存路径
            output_png_path = os.path.join(path, os.path.splitext(file_name)[0] + ".png")
            
            # 创建 PNG
            create_png_with_text(txt, output_png_path)
            print(f"处理完成：{output_png_path}")

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
    line_spacing = 4  # 行间距
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