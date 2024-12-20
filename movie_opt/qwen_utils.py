import os
from dashscope import Generation

class QwenPlusAssistant:
    def __init__(self, api_key=None, model='qwen-plus', result_format="message"):
        """
        初始化QwenPlusAssistant实例。
        
        :param api_key: DashScope API Key，默认从环境变量中读取
        :param model: 使用的模型，默认为'qwen-plus'
        :param result_format: 响应格式，默认为'message'
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.model = model
        self.result_format = result_format
        self.history = []  # 存储对话历史

    def converse(self, message, use_history=False):
        """
        发送消息给Qwen-Plus模型并获取回复。
        
        :param message: 用户输入的消息内容（单个消息）
        :param use_history: 是否使用历史对话，默认不使用
        :return: 模型回复内容或错误信息
        """
        messages = self.history.copy() if use_history else []
        messages.append({'role': 'user', 'content': message})
        
        try:
            response = Generation.call(
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                result_format=self.result_format
            )
            
            if response.status_code == 200:
                reply_content = response.output.choices[0].message.content
                messages.append({'role': 'assistant', 'content': reply_content})
                
                # 如果使用了历史对话，则更新历史记录
                if use_history:
                    self.history = messages
                
                return reply_content
            else:
                return f"请求失败，错误码：{response.code}，错误信息：{response.message}"
        except Exception as e:
            return f"发生错误：{e}"

# 示例使用：
if __name__ == '__main__':
    # 创建QwenPlusAssistant对象
    qwen_assistant = QwenPlusAssistant()
    
    # 第一次对话，不使用历史对话
    reply = qwen_assistant.converse('你是谁？')
    print("模型回复:", reply)
    
    # 第二次对话，使用历史对话
    reply_with_history = qwen_assistant.converse('你能做什么？', use_history=True)
    print("模型回复(带历史):", reply_with_history)