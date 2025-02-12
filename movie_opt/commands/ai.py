import re
from movie_opt.qwen_utils import * 
import os
from movie_opt.utils import *
from datetime import datetime
import requests
import json  # 导入标准库的 json 模块
from movie_opt.qwen_utils import QwenPlusAssistant


# 创建QwenPlusAssistant对象
QWEN_ASSISTANT = None
PHRASE_SET = None # 这个全局set为笔记做准备 set里面包装tuple为("短语","翻译","中文句子","英文句子","短语讲解")
HARD_WORD_SET = None #set里存放tuple为笔记做准备("单词","翻译","音标","中文句子","英文句子")
HARD_WORD_SCORE_MAP = None #key"单词" value"得分")

# 初始化ai.py的方法，只调用一次
def init_ai():
    global QWEN_ASSISTANT, PHRASE_SET, HARD_WORD_SET, HARD_WORD_SCORE_MAP
    try:
        QWEN_ASSISTANT = QwenPlusAssistant()
        PHRASE_SET = set()
        HARD_WORD_SET = set()
        HARD_WORD_SCORE_MAP = {}
        logging.info(f"初始化ai.py成功\n{'-'*22}")
        print(f"初始化ai.py成功\n{'-'*22}")
    except Exception as e:
        logging.error(f"初始化QwenPlusAssistant失败: {e}")
        print(f"初始化QwenPlusAssistant失败: {e}")


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


def get_most_hard_words(cn_str,en_str):
    q = f"这行单词中最不常用并且最复杂的单词是哪个,只需要告诉我英文，无需其他信息：{en_str}"
    reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
    logging.info("提问："+q+"\n回答：\n"+reply+"\n")
    print("提问："+q+"\n回答：\n"+reply+"\n")
    if reply is None or len(reply) == 0 or str(reply).strip()=="没有":
        return None
    most_hard_words = re.findall(r'[a-zA-Z]+', reply)
    if most_hard_words is not None and len(most_hard_words) > 0:
        return list(map(lambda word: word.lower(), most_hard_words))
    else:
        print("没有找到最难的单词")
        return None


def score_for_sentence(en_str):
    q = f"给这个英语句子和单词的难度打分，0到10分的范围，只告诉我分数无需其他任何信息：{en_str}"
    reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
    logging.info("提问："+q+"\n回答：\n"+reply+"\n")
    print("提问："+q+"\n回答：\n"+reply+"\n")
    pattern = r'\d+'# 正则表达式模式匹配所有数字
    matches = re.findall(pattern, reply)# 查找所有匹配的部分
    numbers = [int(match) for match in matches]# 将找到的所有数字字符串转换为整数列表
    if len(numbers) == 0:
        print("没有找到数字")
        return 0
    else:
        return numbers[0]

def score_for_word(most_hard_word,en_str):
    q = f"给这个单词的难度打分，0到10分的范围，只告诉我分数无需其他任何信息：{most_hard_word}"
    reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
    logging.info("提问："+q+"\n回答：\n"+reply+"\n")
    print("提问："+q+"\n回答：\n"+reply+"\n")
    pattern = r'\d+'# 正则表达式模式匹配所有数字
    matches = re.findall(pattern, reply)# 查找所有匹配的部分
    numbers = [int(match) for match in matches]# 将找到的所有数字字符串转换为整数列表
    if len(numbers) == 0:
        print("没有找到数字")
        return 0
    score = numbers[0]
    if score is None:
        print("没有找到数字")
        return 0

    q = f"在{en_str}这句话中{most_hard_word}是名字吗,回答“是”或者“不是”"
    result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
    logging.info("提问："+q+"\n回答：\n"+result+"\n")
    print("提问："+q+"\n回答：\n"+result+"\n")
    result = find_yes_or_no(result)
    if result is None or len(result) == 0 or result.strip()=="是":
        return 0
    
    q = f"在{en_str}这句话中{most_hard_word}是专有名词吗,回答“是”或者“不是”"
    result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
    logging.info("提问："+q+"\n回答：\n"+result+"\n")
    print("提问："+q+"\n回答：\n"+result+"\n")
    result = find_yes_or_no(result)
    if result is None or len(result) == 0 or result.strip()=="是":
        return 0

    return score


def explain_words(most_hard_word):
    replys = []
    for word in most_hard_word:
        first_line = word + " "
        q = f"这个单词：{word}的中文翻译，直接回复翻译结果不要回复其他内容，如果有多个翻译结果用分号隔开"
        reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+reply+"\n")
        print("提问："+q+"\n回答：\n"+reply+"\n")
        first_line += (reply+" ")
        q = f"这个单词：{word}的音标，直接回复音标结果不要回复其他内容，如果有多个音标结果返回第一个"
        reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+reply+"\n")
        print("提问："+q+"\n回答：\n"+reply+"\n")
        first_line += (reply+" ")
        replys.append(first_line)

        q = f"这个单词：{word}的造句，要求例句简单，常用,例句的中文翻译重启一行"
        reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+reply+"\n")
        print("提问："+q+"\n回答：\n"+reply+"\n")
        replys.append("例句 "+reply)
        replys.append("\n")
    if replys == []:
        return None
    return "\n".join(replys)

# 使用本地模型给英语难度评分
def get_english_difficulty_local_llm(most_hard_words,en_str):
    if most_hard_words is None:
        print(f"没有找到最难的单词 en_str:{en_str}")
        raise RuntimeError(f"没有找到最难的单词 en_str:{en_str}")
    word_scores = {}
    for most_hard_word in most_hard_words:
        most_hard_word = most_hard_word.lower()
        if most_hard_word in HARD_WORD_SCORE_MAP.keys():
            logging.info(f"{most_hard_word}已经在HARD_WORD_SCORE_MAP中，直接返回")
            print(f"{most_hard_word}已经在HARD_WORD_SCORE_MAP中，直接返回")
            word_scores[most_hard_word] = HARD_WORD_SCORE_MAP[most_hard_word]
        else:
            score = score_for_word(most_hard_word,en_str)
            HARD_WORD_SCORE_MAP[most_hard_word] = score
            word_scores[most_hard_word] = score
    if len(word_scores) <= 0:
        return 0
    return max(word_scores, key=lambda k: word_scores[k])



# 查询一句话中的短语或者固定搭配
def get_phrase(cn_str,en_str):
    q = f"这句话中“{en_str}”包含哪些英文短语固定搭配或常用俚语,如果没有直接回答“没有”不要回答其他任何内容，如果有直接回答短语和翻译用#分割,不要显示其他无用内容，例如：“Talk about#说到，提及”,如果有多行短语需要换行显示"
    if QWEN_ASSISTANT is None:
        raise RuntimeError("QWEN_ASSISTANT 还没有初始化，请先调用 init_ai()")
    reply = QWEN_ASSISTANT.converse(q)
    logging.info("提问："+q+"\n回答：\n"+reply+"\n")
    print("提问："+q+"\n回答：\n"+reply+"\n")
    if reply is None or len(reply) == 0 or str(reply).strip()=="没有":
        return None
    else:
        # 按行分割输入字符串
        lines = reply.split('\n')
        r = []
        for line in lines:
            # 忽略空行
            if line.strip():
                # 假设英文短语和中文翻译之间用制表符（Tab）分隔
                parts = line.split('#')
                if len(parts) == 2:
                    english_phrase, chinese_translation = parts

            q = f"简短讲解英文短语{english_phrase.strip()}在口语中的用法，及1个使用例句"
            if QWEN_ASSISTANT is None:
                raise RuntimeError("QWEN_ASSISTANT 还没有初始化，请先调用 init_ai()")
            explain = QWEN_ASSISTANT.converse(q)
            logging.info("提问："+q+"\n回答：\n"+explain+"\n")
            print("提问："+q+"\n回答：\n"+explain+"\n")
            r.append((english_phrase.strip(), chinese_translation.strip(), cn_str, en_str, explain))
        PHRASE_SET.update(r)
        return r

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
    logging.info("提问："+q+"\n回答：\n"+result+"\n")
    print("提问："+q+"\n回答：\n"+result+"\n")
    most_hard_words = re.findall(r'[a-zA-Z]+', result)
    for most_hard_word in most_hard_words:
        print(f"对{most_hard_word}进行操作")
        if len(most_hard_word) < 6:
            print(f"{most_hard_word}长度小于6，跳过")
            continue
        score = score_for_word(most_hard_word,en_str)
        if score is None:
            print("单词难度打分没有找到数字")
            continue
        if score < 5:
            print(f"单词难度小于5，跳过")
            continue

        q = f"翻译{most_hard_word}，只显示翻译不显示其他无用内容"
        translation = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+translation+"\n")
        print("提问："+q+"\n回答：\n"+translation+"\n")

        q = f"音标{most_hard_word}，只显示音标不显示其他无用内容"
        result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+result+"\n")
        print("提问："+q+"\n回答：\n"+result+"\n")
        pattern = r"/(.*?)/|\[(.*?)\]" 
        match = re.search(pattern, result)
        phonetic = None
        if match:
            phonetic = match.group(0).replace("[","/").replace("]","/")
            
        
        # q = f"当“{cn_str}”翻译为“{en_str}”其中“{most_hard_word}”这个单词可以被翻译为这中文里的哪个词？只回答词本身，没有翻译就回答“没有”"
        # if QWEN_ASSISTANT is None:
        #     raise RuntimeError("QWEN_ASSISTANT 还没有初始化，请先调用 init_ai()")
        # match_cn_txt = QWEN_ASSISTANT.converse(q)
        # logging.info("提问："+q+"\n回答：\n"+match_cn_txt+"\n")
        # print("提问："+q+"\n回答：\n"+match_cn_txt+"\n")
        # if match_cn_txt is None or len(match_cn_txt) == 0 or match_cn_txt.strip()=="没有":
        #     r.append((most_hard_word, translation, phonetic, None))
        #     HARD_WORD_SET.add((most_hard_word,translation,phonetic,cn_str,en_str))
        #     continue
        # if match_cn_txt in cn_str:
        #     r.append((most_hard_word, translation, phonetic, match_cn_txt))
        # else:
        #     r.append((most_hard_word,translation,phonetic,None))

        # TODO 删除下面3句
        match_cn_txt = None
        HARD_WORD_SET.add((most_hard_word,translation,phonetic,cn_str,en_str))
        r.append((most_hard_word,translation,phonetic,None))


        HARD_WORD_SET.add((most_hard_word,translation,phonetic, match_cn_txt,cn_str,en_str))
    return r
# init_ai()
# print(get_hard_words("那里平坦宽阔、广袤无边、酷热难耐","Where it's flat and immense And the heat is intense"))

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

            # 第一次对话，不使用历史对话
            q = f'下面内容中难度为 {word_level}的英文单词，用python的list包装并且打印,例如：["me","i"],如果为空就响应[]。（不要打印其他无用的话，只响应我一个list数值）:\n{content}'
            print("提问：",q)
            reply = QWEN_ASSISTANT.converse(q)
            if QWEN_ASSISTANT is None:
                raise RuntimeError("QWEN_ASSISTANT 还没有初始化，请先调用 init_ai()")
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

