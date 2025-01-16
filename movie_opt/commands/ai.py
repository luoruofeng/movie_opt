import re
from movie_opt.qwen_utils import * 
import os
from movie_opt.utils import *
from datetime import datetime
import requests
import json  # 导入标准库的 json 模块
from movie_opt.qwen_utils import QwenPlusAssistant

def parse_content(data):
    # 将每个JSON字符串解析为字典
    parsed_data = [json.loads(item) for item in data.splitlines()]
    
    # 根据created_at排序，处理时间格式
    parsed_data.sort(key=lambda x: datetime.strptime(f'{x["created_at"][:-1][:23]}Z', "%Y-%m-%dT%H:%M:%S.%fZ"))
    
    # 提取content并判断done状态
    content = []
    for item in parsed_data:
        if item['done']:
            break
        content.append(item['message']['content'])
    
    # 返回合并后的字符串
    return ''.join(content)


def ask_english_teacher_local_llm(question,model_name="llama3.2"):
    """
    调用本地 Ollama 的 Llama 3.2 模型，作为英语老师回答问题。
    
    :param question: str, 用户提出的问题
    :return: str, 模型的回答
    """
    url = "http://localhost:11434/api/chat"  # 替换为实际的 Ollama 服务地址和端口
    if model_name is None:
        model_name = "llama3.2"
    
    messages = [
        {"role": "system", "content": "你是一位专业的英语老师，擅长中英翻译和英文语法的解析。回答内容简短明了，不要啰嗦。"},
        {"role": "user", "content": question}
    ]
    
    payload = {
        "model": model_name,
        "messages": messages
    }
    
    try:
        # 设置 stream=True 以支持流式响应
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            # 收集所有块，解码为字符串
            full_response = ""
            for chunk in response.iter_content(chunk_size=None):
                full_response += chunk.decode('utf-8')  # 将所有块连接为一个字符串
            txt = parse_content(full_response)
            return txt
    except requests.exceptions.RequestException as e:
        return f"调用模型时发生错误: {str(e)}"
    except ValueError as ve:
        return f"解析响应数据时发生错误: {str(ve)}"
    except KeyError:
        return "返回结果中缺少预期字段。"


# 创建QwenPlusAssistant对象
qwen_assistant = QwenPlusAssistant()
phrase_set = set([])
# 查询一句话中的短语或者固定搭配
def get_phrase(cn_str,en_str):
    q = f"这句话中“{en_str}”包含有英文短语固定搭配吗,如果没有直接回答“没有”不要回答其他任何内容，如果有直接回答短语和翻译,例如：“Talk about 说到，提及”"
    reply = qwen_assistant.converse(q, use_history=True)
    logging.info("提问："+q+"\n回答："+reply+"\n")
    print("提问："+q+"\n回答："+reply+"\n")
    if reply is None or len(reply) == 0 or reply=="没有":
        return None
    
    if reply not in phrase_set:
        phrase_set.add(reply)
    else:
        return

    q = f"讲解这个短语"
    result = qwen_assistant.converse(q, use_history=True)
    logging.info("提问："+q+"\n回答："+result+"\n")
    print("提问："+q+"\n回答："+result+"\n")
    return result


def find_yes_or_no(text):
    pattern = r'不是|是'  # 先匹配 “不是”，再匹配 “是”
    matches = re.findall(pattern, text)
    if len(matches) > 0:
        return matches[0]
    return None

# 询问每句话最难得单词是哪个
def get_hard_words(cn_str,en_str):
    r = [] #包括元组
    q = f"这句话中最难的单词是哪几个:{en_str}"
    result = ask_english_teacher_local_llm(q)
    logging.info("提问："+q+"\n回答："+result+"\n")
    print("提问："+q+"\n回答："+result+"\n")
    most_hard_words = re.findall(r'[a-zA-Z]+', result)
    for most_hard_word in most_hard_words:
        if len(most_hard_word) < 6:
            r.append((None,None,None,None))
            continue
        
        q = f"在{en_str}这句话中{most_hard_word}是名字吗,回答“是”或者“不是”"
        result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答："+result+"\n")
        print("提问："+q+"\n回答："+result+"\n")
        result = find_yes_or_no(result)
        if result is None or len(result) == 0 or result.strip()=="是":
            r.append((None,None,None,None))
            continue
        
        q = f"在{en_str}这句话中{most_hard_word}是专有名词吗,回答“是”或者“不是”"
        result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答："+result+"\n")
        print("提问："+q+"\n回答："+result+"\n")
        result = find_yes_or_no(result)
        if result is None or len(result) == 0 or result.strip()=="是":
            r.append((None,None,None,None))
            continue

        q = f"翻译{most_hard_word}，只显示翻译不显示其他无用内容"
        translation = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答："+translation+"\n")
        print("提问："+q+"\n回答："+translation+"\n")

        q = f"音标{most_hard_word}，只显示音标不显示其他无用内容"
        result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答："+result+"\n")
        print("提问："+q+"\n回答："+result+"\n")
        pattern = r"/(.*?)/|\[(.*?)\]" 
        match = re.search(pattern, result)
        phonetic = None
        if match:
            phonetic = match.group(1)  # 只提取音标部分
            
        q = f"将“{en_str}”翻译为： “{cn_str}”。“{most_hard_word}”这个单词是直译的吗？回答“是”或“不是”"
        result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答："+result+"\n")
        print("提问："+q+"\n回答："+result+"\n")
        result = find_yes_or_no(result)
        if result is None or len(result) == 0 or result.strip()=="不是":
            r.append((most_hard_word, translation, phonetic, None))
            continue
        
        q = f"在“{cn_str}”中“{most_hard_word}”这个单词被翻译为哪个词？只回答词本身，没有翻译就回答“没有”"
        match_cn_txt = qwen_assistant.converse(q)
        logging.info("提问："+q+"\n回答："+match_cn_txt+"\n")
        print("提问："+q+"\n回答："+match_cn_txt+"\n")
        if match_cn_txt is None or len(match_cn_txt) == 0 or match_cn_txt.strip()=="没有":
            r.append((most_hard_word, translation, phonetic, None))
            continue

        r.append((most_hard_word,translation,phonetic,match_cn_txt))
    return r
print(get_hard_words("那里只有一群会暗箭伤人的 可怕的荒原人","Nothing there but a bunch of backstabbing, murderous outsiders."))



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

