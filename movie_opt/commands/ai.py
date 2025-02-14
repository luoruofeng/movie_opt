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
SENTENCE_SCORE_MAP = None #key"单词" value"得分")

# 初始化ai.py的方法，只调用一次
def init_ai():
    global QWEN_ASSISTANT, PHRASE_SET, HARD_WORD_SET, HARD_WORD_SCORE_MAP,SENTENCE_SCORE_MAP
    try:
        QWEN_ASSISTANT = QwenPlusAssistant()
        PHRASE_SET = set()
        HARD_WORD_SET = set()
        HARD_WORD_SCORE_MAP = {}
        SENTENCE_SCORE_MAP = {}
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
    q = f"这行英文句子：{en_str} 中，哪个单词或短语最复杂,只需要告诉我答案不要修改内容和格式不要添加其他符号如下划线，如果有多个难的单词或词组使用竖线分割他们,无需回答其他任何信息。"
    if QWEN_ASSISTANT is None:
        raise RuntimeError("QWEN_ASSISTANT 还没有初始化，请先调用 init_ai()")
    reply = QWEN_ASSISTANT.converse(q)
    logging.info("提问："+q+"\n回答：\n"+reply+"\n")
    print("提问："+q+"\n回答：\n"+reply+"\n")
    if reply is None or len(reply) == 0 or str(reply).strip()=="没有":
        return None
    else:
        most_hard_words = reply.strip().split("|")
        if most_hard_words is not None and len(most_hard_words) > 0:
            most_hard_words = list(map(lambda x: x.strip(), most_hard_words))
            return list(map(lambda x: x.lower(), most_hard_words))
        else:
            print("没有找到最难的单词")
            return None
    # 本地查询不准
    # reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
    # logging.info("提问："+q+"\n回答：\n"+reply+"\n")
    # print("提问："+q+"\n回答：\n"+reply+"\n")
    # if reply is None or len(reply) == 0 or str(reply).strip()=="没有":
    #     return None
    # most_hard_words = reply.strip().split("|")
    # if most_hard_words is not None and len(most_hard_words) > 0:
    #     most_hard_words = list(map(lambda x: x.strip(), most_hard_words))
    #     return list(map(lambda x: x.lower(), most_hard_words))
    # else:
    #     print("没有找到最难的单词")
    #     return None

def split_sentence(en_str):
    q = f"找出句子中自然的停顿点或者意思转折的地方进行分割,只返回分割句子的内容，无关内容不返回，风格用竖线完成，句子：{en_str}"
    reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
    logging.info("提问："+q+"\n回答：\n"+reply+"\n")
    print("提问："+q+"\n回答：\n"+reply+"\n")
    subsentences = reply.split("|")
    if subprocess is None or subprocess.strip() == "":
        return None
    return subsentences


def score_for_sentence(en_content):
    sentence_score = SENTENCE_SCORE_MAP[en_content]
    if sentence_score is not None:
        return sentence_score
    sentence_score = 0
    try:
        q = f"给这个英语句子和单词的难度打分，0到10分的范围，只告诉我分数无需其他任何信息：{en_content}"
        reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+reply+"\n")
        print("提问："+q+"\n回答：\n"+reply+"\n")
        pattern = r'\d+'# 正则表达式模式匹配所有数字
        matches = re.findall(pattern, reply)# 查找所有匹配的部分
        numbers = [int(match) for match in matches]# 将找到的所有数字字符串转换为整数列表
        if len(numbers) == 0:
            print("score_for_sentence-没有找到数字")
        else:
            sentence_score = numbers[0]
        return sentence_score
    finally:
        SENTENCE_SCORE_MAP[en_content] = sentence_score

def score_for_word(most_hard_word,en_str):
    most_hard_word = most_hard_word.lower()
    if most_hard_word in HARD_WORD_SCORE_MAP.keys():
        logging.info(f"{most_hard_word}已经在HARD_WORD_SCORE_MAP中")
        print(f"{most_hard_word}已经在HARD_WORD_SCORE_MAP中")
        return HARD_WORD_SCORE_MAP[most_hard_word]
    score = 0
    try:
        q = f"给这个单词的难度打分，0到10分的范围，只告诉我分数无需其他任何信息：{most_hard_word}"
        reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+reply+"\n")
        print("提问："+q+"\n回答：\n"+reply+"\n")
        pattern = r'\d+'# 正则表达式模式匹配所有数字
        matches = re.findall(pattern, reply)# 查找所有匹配的部分
        numbers = [int(match) for match in matches]# 将找到的所有数字字符串转换为整数列表
        if len(numbers) == 0:
            print("没有找到数字")
            logging.info(f"score_for_word {most_hard_word}没有找到数字得分")
            return score
        score = int(numbers[0])

        q = f"在{en_str}这句话中是否存在{most_hard_word}这个单词。如果存在直接返回“是”，否则返回“否”"
        result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+result+"\n")
        print("提问："+q+"\n回答：\n"+result+"\n")
        result = find_yes_or_no(result)
        if result is None or len(result) == 0 or result.strip()=="否":
            score = 0
            return score

        q = f"在{en_str}这句话中{most_hard_word}这个单词是不存在的错误单词或拼写错误吗？如果是错误的直接返回“是”，否则返回“否”"
        result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+result+"\n")
        print("提问："+q+"\n回答：\n"+result+"\n")
        result = find_yes_or_no(result)
        if result is None or len(result) == 0 or result.strip()=="是":
            score = 0
            return score


        q = f"在{en_str}这句话中{most_hard_word}是名字吗,回答“是”或者“不是”"
        result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+result+"\n")
        print("提问："+q+"\n回答：\n"+result+"\n")
        result = find_yes_or_no(result)
        if result is None or len(result) == 0 or result.strip()=="是":
            score = 0
            return score
        
        q = f"在{en_str}这句话中{most_hard_word}是专有名词吗,回答“是”或者“不是”"
        result = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+result+"\n")
        print("提问："+q+"\n回答：\n"+result+"\n")
        result = find_yes_or_no(result)
        if result is None or len(result) == 0 or result.strip()=="是":
            score = 0
            return score
        return score
    finally:
        HARD_WORD_SCORE_MAP[most_hard_word] = score
        logging.info(f"单词{most_hard_word}得分 {score} 存入HARD_WORD_SCORE_MAP中")
        print(f"单词{most_hard_word}得分 {score} 存入HARD_WORD_SCORE_MAP中")

def explain_words(most_hard_word):
    replys = []
    en_cn = {}
    for word in most_hard_word:
        first_line = word + " "
        q = f"这个单词：{word}的中文翻译，直接回复翻译结果不要回复其他内容，如果有多个翻译结果用分号隔开，如果这样的单词不存在或拼写错误直接返回“单词错误”"
        reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+reply+"\n")
        print("提问："+q+"\n回答：\n"+reply+"\n")
        if reply.strip() == "单词错误":
            logging.error(f"解释单词，传入的单词错误 {word}")
            continue
        first_line += (reply+" ")
        en_cn[word] = reply
        # q = f"这个单词：{word}的音标，直接回复音标结果不要回复其他内容，如果有多个音标结果返回第一个"
        # reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        # logging.info("提问："+q+"\n回答：\n"+reply+"\n")
        # print("提问："+q+"\n回答：\n"+reply+"\n")
        # first_line += (reply+" ")
        replys.append(first_line)

        q = f"这个单词：{word}的造一句例句，要求例句简单，常用,例句的中文翻译重启一行"
        reply = ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+reply+"\n")
        print("提问："+q+"\n回答：\n"+reply+"\n")
        reply = add_indent_to_str(reply)
        replys.append("例句：\n"+reply+"\n")
        replys.append("-----------------------")
    if replys == []:
        return None
    replys.pop()
    return "\n".join(replys), en_cn




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
    pattern = r'不是|是|否'  # 先匹配 “不是”，再匹配 “是”，再匹配 “否”
    matches = re.findall(pattern, text)
    if len(matches) > 0:
        return matches[0]
    return None



# 句子和最难的单词低于指定分数返回空，否则返回所有高于指定分数的最难的单词
def get_hard_word_scores(cn_content,en_content,filter_score=5):
    sentence_score = score_for_sentence(en_content)
    if sentence_score <= filter_score:
        logging.info(f"get_hard_word_scores-退出-语句分数低于{filter_score}分 en_content:{en_content}")
        return None

    most_hard_words = get_most_hard_words(cn_content,en_content)
    if most_hard_words is not None and len(most_hard_words) > 0:
        most_hard_word_score = {}
        # 找出最难得单词的得分
        for hard_word in most_hard_words:
            s = score_for_word(hard_word,en_content)
            if s > filter_score:
                most_hard_word_score[hard_word] = s
            else:
                logging.info(f"get_hard_word_scores-忽略单词{hard_word}-分数低于{filter_score} en_content:{en_content}")
                continue
        most_hard_word = max(most_hard_word_score, key=lambda k: most_hard_word_score[k])
        score = most_hard_word_score[most_hard_word]
        if score < filter_score:
            logging.info(f"get_hard_word_scores-退出-最难的单词{most_hard_word}-分数低于{filter_score}分 en_content:{en_content}")
            return None
        else:
            logging.info(f"get_hard_word_scores-最难的单词{most_hard_word}-分数高于{filter_score}分 en_content:{en_content}")
        return most_hard_word_score
    else:
        return None

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

