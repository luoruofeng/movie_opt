from pathlib import Path
from pypdf import PdfReader
from pathlib import Path
import re
from movie_opt.commands.voice import edge_tts_voice
from movie_opt.utils import *
import os
import argparse
import subprocess
import shutil

# 替换一些符号为逗号，为了edge_tts可以朗读的时候断句
def replace_punctuation(input_file_path):
    """
    Replace Chinese punctuation with a Chinese comma, and English punctuation with an English comma in the given text file.

    :param input_file_path: Path to the input text file.
    """
    # Define the punctuation replacements
    punctuation_replacements = {
        '：': '，',  # Chinese colon to Chinese comma
        '、': '，',  # Chinese enumerator to Chinese comma
        '？': '，',  # Chinese question mark to Chinese comma
        '；': '，',  # Chinese semicolon to Chinese comma
        '！': '，',  # Chinese exclamation mark to Chinese comma
        ':': ',',   # English colon to English comma
        ',': ',',   # English comma remains unchanged
        '?': ',',   # English question mark to English comma
        ';': ',',   # English semicolon to English comma
        '!': ',',   # English exclamation mark to English comma
    }

    # Read the content of the input file
    with open(input_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Replace the punctuation marks
    for old_punct, new_punct in punctuation_replacements.items():
        content = content.replace(old_punct, new_punct)

    # Save the modified content back to the same file (overwrite)
    with open(input_file_path, 'w', encoding='utf-8') as file:
        file.write(content)

# 去除乱码
def clean_txt_of_garbled(file_path):
    """
    清除 TXT 文件中的乱码并重新保存。

    :param file_path: str, 要处理的 TXT 文件路径
    """
    try:
        # 读取原始 TXT 文件内容
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # 使用正则表达式保留中文、英文、数字和常见符号
        # 在正则表达式中添加顿号（、）和其他标点符号
        pattern = r'[^\u4e00-\u9fa5a-zA-Z0-9\s,.!?;:\-"\'()\[\]{}<>《》—，。！？；：“”‘’（）【】、]'  
        garbled_parts = re.findall(pattern, content)  # 查找乱码部分
        cleaned_content = re.sub(pattern, '', content)  # 去除乱码部分

        # 打印清除的乱码部分
        if garbled_parts:
            print("清除的乱码部分:", ''.join(set(garbled_parts)))  # 去重并打印
        else:
            print("未发现明显的乱码部分。")

        # 将清理后的内容重新保存到原始文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(cleaned_content)

        print(f"文件 {file_path} 中的乱码已清除，并成功保存！")
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")




def merge_short_sentences(sentences):
    """
    Merge adjacent strings in a list so that each resulting string has at least 150 characters.

    Args:
        sentences (list): A list of strings.

    Returns:
        list: A new list with merged strings.
    """
    if not sentences:
        return []

    merged_sentences = []
    buffer = ""

    for sentence in sentences:
        buffer += sentence
        if len(buffer) >= 250:
            merged_sentences.append(buffer)
            buffer = ""

    # Add any remaining content in the buffer
    if buffer:
        merged_sentences.append(buffer)

    return merged_sentences

def split_sentences_2voice(args):
    def process_txt(txt_path):
        print(f"生成音频：{txt_path}")
        # 读取txt文件内容
        with open(txt_path, 'r', encoding='utf-8') as file:
            text = file.read()

        # 匹配中文和英文标点符号作为分句符，省略号，冒号，分号等也包括在内
        sentence_delimiters = r'[。！？\.!?：；…]'

        # 匹配双引号内的内容，并保留为一行
        quoted_pattern = r'".*?"'

        # 用于存储结果的列表
        result = []

        # 找到所有双引号括起来的内容
        quoted_matches = re.finditer(quoted_pattern, text)
        start_idx = 0

        for match in quoted_matches:
            # 提取双引号前的内容
            pre_text = text[start_idx:match.start()]
            if pre_text:
                result.extend(re.split(sentence_delimiters, pre_text))

            # 提取双引号内的内容
            result.append(match.group())
            start_idx = match.end()

        # 处理最后一段文本
        remaining_text = text[start_idx:]
        if remaining_text:
            result.extend(re.split(sentence_delimiters, remaining_text))

        # 去除空字符串并返回结果
        sentences = [sentence.strip() for sentence in result if sentence.strip()]
        sentences = merge_short_sentences(sentences)
        # 设置临时目录和参数
        args = argparse.ArgumentParser()
        args.language = "zh-cn"
        args.voice = None
        filename = os.path.splitext(os.path.basename(txt_path))[0]
        temp_dir = f"{os.path.join(os.path.dirname(txt_path),filename)}"
        
        # 删除临时文件
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir) 
        os.makedirs(temp_dir, exist_ok=True)

        # 保存分句的音频文件
        for i, sentence in enumerate(sentences):
            args.save_path = os.path.join(temp_dir, f"temp_{i}.mp3")
            args.content = sentence
            edge_tts_voice(args)

        # TODO: ffmpeg 拼接所有 MP3 文件，保存为最终文件
        output_mp3 = os.path.join(os.path.dirname(txt_path) ,f"{filename}.mp3")
        concat_file = f"{temp_dir}/file_list.txt"

        with open(concat_file, 'w', encoding='utf-8') as concat:
            for i in range(len(sentences)):
                concat.write(f"file 'temp_{i}.mp3'\n")
        missing, duplicates = check_file_numbers(concat_file)
        if len(missing) > 0 or len(concat_file) > 0:
            return
        
        command = [
            "ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_mp3
        ]
        print(" ".join(command))
        # 执行命令并捕获错误信息
        result = subprocess.run(
            command, 
            check=True, 
            stderr=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            text=True,
            encoding="utf-8"
        )
        # 删除临时文件
        shutil.rmtree(temp_dir)  # 强制删除文件夹及其内容

    txt_path = args.path

    # 检查路径是否存在
    if not os.path.exists(txt_path):
        print(f"路径 {txt_path} 不存在！")
        return

    # 如果是单个文件且为 PDF，则直接操作
    if os.path.isfile(txt_path) and get_file_extension(txt_path) == ".txt":
        process_txt(txt_path)
    # 如果是目录，则遍历目录中所有 txt 文件
    elif os.path.isdir(txt_path):
        for file in os.listdir(txt_path):  # 遍历目录及子目录的 txt 文件
            txt_file = None
            if file.endswith(".txt"):
                txt_file = file
            else:
                continue
            try:
                process_txt(os.path.join(txt_path,txt_file))
            except Exception as e:
                logging.error(e)
    else:
        raise RuntimeError("请传入txt文件路径")
    

def remove_numbers_from_txt(file_path):
    """
    从指定txt文件中删除所有数字。

    Args:
        file_path (str): txt文件的路径。
    """

    with open(file_path, 'r+', encoding='utf-8') as file:
        content = file.read()
        # 使用正则表达式替换所有数字为空字符串
        new_content = re.sub(r'\[\d+\]', '', content)
        new_content = re.sub(r'\(\d+\)', '', new_content)
        new_content = re.sub(r'【\d+】', '', new_content)
        new_content = re.sub(r'（\d+）', '', new_content)
        # 将修改后的内容写回文件开头，覆盖原内容
        file.seek(0)
        file.write(new_content)
        file.truncate()


def remove_parentheses_content(file_path):
    """
    从指定txt文件中删除所有小括号括起来的内容，包括小括号本身。

    Args:
        file_path (str): txt文件的路径。
    """

    with open(file_path, 'r+', encoding='utf-8') as file:
        content = file.read()
        # 使用正则表达式替换所有小括号及其内容为空字符串
        new_content = re.sub(r'\(.*?\)', '', content)
        # 将修改后的内容写回文件开头，覆盖原内容
        file.seek(0)
        file.write(new_content)
        file.truncate()

#对pdf结构化的支持不好 
def pdf_to_txt_pypdf(args):
    
    def process_pdf(pdf_file):
        """
        处理单个 PDF 文件，将其内容按页识别并写入同名的 TXT 文件。
        """
        try:
            print(f"正在处理文件: {pdf_file}")

            # 创建一个 PDF 阅读器
            reader = PdfReader(pdf_file)

            # 保存 TXT 文件路径（与 PDF 文件同目录同名）
            txt_file = pdf_file.with_suffix(".txt")

            # 打开 TXT 文件以写入内容
            with open(txt_file, "w", encoding="utf-8") as txt:
                for page_num, page in enumerate(reader.pages):
                    # 读取每页内容并进行处理
                    text = page.extract_text()
                    if text:
                        text = text.replace('\n',"")
                        # 将文本按行分割成段落
                        paragraphs = text.split('\n')
                        formatted_text = ""

                        # 处理每个段落，添加两个空格
                        for paragraph in paragraphs:
                            paragraph = paragraph.strip()
                            if paragraph:
                                formatted_text += f"{paragraph}"

                        # 写入到文件
                        txt.write(formatted_text)
            print(f"已保存为 TXT 文件: {txt_file}")
            remove_numbers_from_txt(txt_file) #删除 [数字] 样式的内容
            remove_parentheses_content(txt_file) #删除所有小括号括起来的内容
            clean_txt_of_garbled(txt_file) # 清理乱码
            replace_punctuation(txt_file) #修改标点符号为逗号
        except Exception as e:
            print(f"处理文件 {pdf_file} 时出错: {e}")

    path = args.path

    # 将路径转换为 Path 对象，方便处理
    path_obj = Path(path)

    # 检查路径是否存在
    if not path_obj.exists():
        print(f"路径 {path} 不存在！")
        return

    # 如果是单个文件且为 PDF，则直接操作
    if path_obj.is_file() and path_obj.suffix.lower() == ".pdf":
        process_pdf(path_obj)
    # 如果是目录，则遍历目录中所有 PDF 文件
    elif path_obj.is_dir():
        for pdf_file in path_obj.rglob("*.pdf"):  # 遍历目录及子目录的 PDF 文件
            process_pdf(pdf_file)
    else:
        print(f"路径 {path} 既不是 PDF 文件，也不是目录。")
        return
    


import pdfplumber
from pathlib import Path
#对pdf结构化的支持较好 无法识别顿号
def pdf_to_txt_pdfplumber(args):
    
    def process_pdf(pdf_file):
        """
        处理单个 PDF 文件，将其内容按页识别并写入同名的 TXT 文件。
        """
        try:
            print(f"正在处理文件: {pdf_file}")

            # 使用 pdfplumber 打开 PDF 文件
            with pdfplumber.open(pdf_file) as pdf:
                # 保存 TXT 文件路径（与 PDF 文件同目录同名）
                txt_file = pdf_file.with_suffix(".txt")

                # 打开 TXT 文件以写入内容
                with open(txt_file, "w", encoding="utf-8") as txt:
                    for page_num, page in enumerate(pdf.pages):
                        # 使用 pdfplumber 提取每页的文本
                        text = page.extract_text()
                        if text:
                            # text = text.replace('\n', "")  # 去掉换行符
                            # 将文本按行分割成段落
                            paragraphs = text.split('\n')
                            formatted_text = ""

                            # 处理每个段落，添加两个空格
                            for paragraph in paragraphs:
                                paragraph = paragraph.strip()
                                if paragraph:
                                    formatted_text += f"{paragraph}"

                            # 写入到文件
                            txt.write(formatted_text)
            print(f"已保存为 TXT 文件: {txt_file}")
            remove_numbers_from_txt(txt_file)  # 删除 [数字] 样式的内容
            remove_parentheses_content(txt_file)  # 删除所有小括号括起来的内容
            clean_txt_of_garbled(txt_file)  # 清理乱码
            replace_punctuation(txt_file)  # 修改标点符号为逗号
        except Exception as e:
            print(f"处理文件 {pdf_file} 时出错: {e}")

    path = args.path

    # 将路径转换为 Path 对象，方便处理
    path_obj = Path(path)

    # 检查路径是否存在
    if not path_obj.exists():
        print(f"路径 {path} 不存在！")
        return

    # 如果是单个文件且为 PDF，则直接操作
    if path_obj.is_file() and path_obj.suffix.lower() == ".pdf":
        process_pdf(path_obj)
    # 如果是目录，则遍历目录中所有 PDF 文件
    elif path_obj.is_dir():
        for pdf_file in path_obj.rglob("*.pdf"):  # 遍历目录及子目录的 PDF 文件
            process_pdf(pdf_file)
    else:
        print(f"路径 {path} 既不是 PDF 文件，也不是目录。")
        return


import argparse
args = argparse.Namespace()
args.path = r"C:\Users\luoruofeng\Desktop\test5"
if __name__ == "__main__":
    pdf_to_txt_pdfplumber(args)
    split_sentences_2voice(args)