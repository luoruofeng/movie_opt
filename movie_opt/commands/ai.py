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

def find_yes_or_no(text):
    pattern = r'不是|是|否'  # 先匹配 “不是”，再匹配 “是”，再匹配 “否”
    matches = re.findall(pattern, text)
    if len(matches) > 0:
        return matches[0]
    return None


QWEN_ASSISTANT = None

class LaunageAI:
    def __init__(self):
        print(f"初始化LaunageAI\n{'-'*22}")
        logging.info(f"初始化LaunageAI\n{'-'*22}")
        self.local_model_url = "http://localhost:11434/api/chat"  # 替换为实际的 Ollama 服务地址和端口
        # 初始化ai.py的方法，只调用一次
        self.init_ai()

    # 初始化ai.py的方法，只调用一次
    def init_ai(self):
        try:
            global QWEN_ASSISTANT
            QWEN_ASSISTANT = QwenPlusAssistant()
            logging.info(f"初始化QWEN.py成功\n{'-'*22}")
            print(f"初始化QWEN成功\n{'-'*22}")
            self.hard_word_score_map = {} #key"单词" value"得分")
            self.sentence_score_map = {} #key"单词" value"得分")
            logging.info(f"初始化ai.py成功\n{'-'*22}")
            print(f"初始化ai.py成功\n{'-'*22}")
        except Exception as e:
            logging.error(f"初始化QwenPlusAssistant失败: {e}")
            print(f"初始化QwenPlusAssistant失败: {e}")




    def ask_english_teacher_local_llm(self,question,model_name="qwen2.5:14b"):
        """
        调用本地 Ollama 的 Llama 3.2 模型，作为英语老师回答问题。
        
        :param question: str, 用户提出的问题
        :return: str, 模型的回答
        """
        local_model_pre_messages = [
            {"role": "system", "content": "你是一位专业的英语老师，擅长中英翻译和英文语法的解析。回答内容简短明了，不要啰嗦。"}
        ]
        local_model_pre_messages.append({"role": "user", "content": question})

        payload = {
            "model": model_name,
            "messages": local_model_pre_messages
        }
        
        try:
            # 设置 stream=True 以支持流式响应
            with requests.post(self.local_model_url, json=payload, stream=True) as response:
                response.raise_for_status()
                # 收集所有块，解码为字符串
                full_response = ""
                for chunk in response.iter_content(chunk_size=None):
                    full_response += chunk.decode('utf-8')  # 将所有块连接为一个字符串
                txt = parse_content(full_response)
                return txt
        except requests.exceptions.RequestException as e:
            return f"ask_english_teacher_local_llm-调用模型时发生错误: {str(e)}"
        except ValueError as ve:
            return f"ask_english_teacher_local_llm-解析响应数据时发生错误: {str(ve)}"
        except KeyError:
            return "ask_english_teacher_local_llm-返回结果中缺少预期字段。"


    def get_most_hard_words(self,cn_str,en_str):
        q = f"这行英文句子：{en_str} 中，哪个单词或短语最复杂,只需要告诉我答案不要修改内容和格式不要添加其他符号如下划线，如果有多个难的单词或词组使用竖线分割他们,无需回答其他任何信息。"
        if QWEN_ASSISTANT is None:
            raise RuntimeError("QWEN_ASSISTANT 还没有初始化，请先调用 init_ai()")
        reply = QWEN_ASSISTANT.converse(q)
        logging.info("提问："+q+"\n回答：\n"+reply+"\n") # type: ignore
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
        # reply = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
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

    def split_sentence(self,en_str):
        q = f"找出句子中自然的停顿点或者意思转折的地方进行分割,只返回分割句子的内容，无关内容不返回，风格用竖线完成，句子：{en_str}"
        reply = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
        logging.info("提问："+q+"\n回答：\n"+reply+"\n")
        print("提问："+q+"\n回答：\n"+reply+"\n")
        subsentences = reply.split("|")
        if subprocess is None or subprocess.strip() == "":
            return None
        return subsentences


    def score_for_sentence(self,en_content):
        if en_content in self.sentence_score_map.keys():
            sentence_score = self.sentence_score_map[en_content]
            if sentence_score is not None:
                print(f"score_for_sentence-已经在self.sentence_score_map中 {en_content}")
                logging.info(f"score_for_sentence-已经在self.sentence_score_map中 {en_content}")
                return sentence_score
        sentence_score = 0
        try:
            q = f"给这个英语句子的难度打分，0到10分的范围，只告诉我分数无需其他任何信息：{en_content}"
            reply = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
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
            self.sentence_score_map[en_content] = sentence_score

    def score_for_word(self,most_hard_word,en_str):
        most_hard_word = most_hard_word.lower()
        if most_hard_word in self.hard_word_score_map.keys():
            logging.info(f"{most_hard_word}已经在self.hard_word_score_map中")
            print(f"{most_hard_word}已经在self.hard_word_score_map中")
            return self.hard_word_score_map[most_hard_word]
        score = 0
        try:
            q = f"给这个单词的难度打分，0到10分的范围，只告诉我分数无需其他任何信息：{most_hard_word}"
            reply = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
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
            result = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
            logging.info("提问："+q+"\n回答：\n"+result+"\n")
            print("提问："+q+"\n回答：\n"+result+"\n")
            result = find_yes_or_no(result)
            if result is None or len(result) == 0 or result.strip()=="否":
                score = 0
                return score

            q = f"在{en_str}这句话中{most_hard_word}这个单词是不存在的错误单词或拼写错误吗？如果是错误的直接返回“是”，否则返回“否”"
            result = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
            logging.info("提问："+q+"\n回答：\n"+result+"\n")
            print("提问："+q+"\n回答：\n"+result+"\n")
            result = find_yes_or_no(result)
            if result is None or len(result) == 0 or result.strip()=="是":
                score = 0
                return score


            q = f"在{en_str}这句话中{most_hard_word}是名字吗,回答“是”或者“否”"
            result = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
            logging.info("提问："+q+"\n回答：\n"+result+"\n")
            print("提问："+q+"\n回答：\n"+result+"\n")
            result = find_yes_or_no(result)
            if result is None or len(result) == 0 or result.strip()=="是":
                score = 0
                return score
            
            q = f"在{en_str}这句话中{most_hard_word}是专有名词吗,回答“是”或者“否”"
            result = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
            logging.info("提问："+q+"\n回答：\n"+result+"\n")
            print("提问："+q+"\n回答：\n"+result+"\n")
            result = find_yes_or_no(result)
            if result is None or len(result) == 0 or result.strip()=="是":
                score = 0
                return score
            return score
        finally:
            self.hard_word_score_map[most_hard_word] = score
            logging.info(f"单词{most_hard_word}得分 {score} 存入self.hard_word_score_map中")
            print(f"单词{most_hard_word}得分 {score} 存入self.hard_word_score_map中")

    def explain_words(self,most_hard_word):
        replys = []
        en_cn = {}
        for word in most_hard_word:
            first_line = word + " "
            q = f"这个单词：{word}的中文翻译，直接回复翻译结果不要回复其他内容，如果有多个翻译结果用分号隔开，如果这样的单词不存在或拼写错误直接返回“单词错误”"
            reply = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
            logging.info("提问："+q+"\n回答：\n"+reply+"\n")
            print("提问："+q+"\n回答：\n"+reply+"\n")
            if reply.strip() == "单词错误":
                logging.error(f"解释单词，传入的单词错误 {word}")
                continue
            first_line += (reply+" ")
            en_cn[word] = reply
            # q = f"这个单词：{word}的音标，直接回复音标结果不要回复其他内容，如果有多个音标结果返回第一个"
            # reply = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
            # logging.info("提问："+q+"\n回答：\n"+reply+"\n")
            # print("提问："+q+"\n回答：\n"+reply+"\n")
            # first_line += (reply+" ")
            replys.append(first_line)

            q = f"这个单词：{word}的造一句例句，要求例句简单，常用,例句的中文翻译重启一行"
            reply = self.ask_english_teacher_local_llm(q,model_name="qwen2.5:14b")
            logging.info("提问："+q+"\n回答：\n"+reply+"\n")
            print("提问："+q+"\n回答：\n"+reply+"\n")
            reply = add_indent_to_str(reply)
            replys.append("例句：\n"+reply+"\n")
            replys.append("----------------------------")
        if replys == []:
            return None,None
        replys.pop()
        return "\n".join(replys), en_cn




    # 句子和最难的单词低于指定分数返回空，否则返回所有高于指定分数的最难的单词
    def get_hard_word_scores(self,cn_content,en_content,filter_score=1):
        sentence_score = self.score_for_sentence(en_content)
        if sentence_score <= filter_score:
            logging.info(f"get_hard_word_scores-退出-语句分数低于{filter_score}分 en_content:{en_content}")
            return None

        most_hard_words = self.get_most_hard_words(cn_content,en_content)
        if most_hard_words is not None and len(most_hard_words) > 0:
            most_hard_word_score = {}
            # 找出最难得单词的得分
            for hard_word in most_hard_words:
                s = self.score_for_word(hard_word,en_content)
                if s > filter_score:
                    most_hard_word_score[hard_word] = s
                else:
                    logging.info(f"get_hard_word_scores-忽略单词{hard_word}-分数低于{filter_score} en_content:{en_content}")
                    continue
            if most_hard_word_score is None or len(most_hard_word_score) < 1:
                return None
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
