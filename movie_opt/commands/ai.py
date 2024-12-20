from movie_opt.qwen_utils import * 
import os
from movie_opt.utils import *

def get_hard_words_and_set_color(args):
    path = args.path
    word_level = args.level
    if word_level is None:
        word_level = "4级"

    # 检查路径是否为空或不是一个有效的文件路径
    if not path:
        raise ValueError("文件路径不能为空")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"文件路径不存在: {path}")
    
    if not os.path.isfile(path):
        raise IsADirectoryError(f"提供的路径是一个目录而不是文件: {path}")

    # 确认文件是 .txt 文件
    if not path.lower().endswith('.txt') and not path.lower().endswith('.srt') :
        raise ValueError(f"提供的文件不是 .txt .srt 文件: {path}")

    # 读取并打印文件内容
    try:
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            # print(f"文件内容如下：\n{content}")

            # 创建QwenPlusAssistant对象
            qwen_assistant = QwenPlusAssistant()

            # 第一次对话，不使用历史对话
            q = f'下面内容中难度为 {word_level}的英文单词，用python的list包装并且打印,例如：["me","i"],如果为空就响应[]。（不要打印其他无用的话，只响应我一个list数值）:\n{content}'
            print("提问：",q)
            reply = qwen_assistant.converse(q)
            print("模型回复:", reply)

            if is_list_of_strings(reply):
                reply = string_to_list(reply)
            else:
                return {}
            
            if reply == None or len(reply) < 1:
                return {}
            
            r = assign_colors([reply]) if is_list_of_strings(reply) else {}
            print("获取单词和对应的颜色的返回值",r)
            return r
    except IOError as e:
        print(f"无法读取文件: {e}")

