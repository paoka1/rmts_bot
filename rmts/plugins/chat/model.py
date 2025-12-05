from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam
from openai.types.chat import ChatCompletionUserMessageParam
from openai.types.chat import ChatCompletionAssistantMessageParam

from typing import List, Union

from .history import save_messages_to_file, load_messages_from_file
from .prompt import prompt

class Model:

    def __init__(self,
                 *,
                 group_id: int,
                 key: str,
                 base_url: str = "https://api.deepseek.com",
                 model: str = "deepseek-chat",
                 prompt: str = prompt,
                 max_history: int = 10
    ) -> None:
        """
        参数：
            group_id: 群号
            key: deepseek API 密钥
            base_url: API 基础 URL
            model: 使用的模型名称
            prompt: 系统提示语
            max_history: 最大历史消息条数
        """

        self.client: OpenAI
        self.group_id = group_id
        self.key = key
        self.base_url = base_url
        self.model = model
        self.prompt = prompt
        self.max_history = max_history
        self.messages: List[Union[ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam]] = []

        # 读取历史消息
        messages = self.load_messages()
        if messages == []:
            # 初始化历史消息列表，包含系统提示
            self.messages.append(ChatCompletionSystemMessageParam(content=self.prompt, role="system"))
        else:
            self.messages = messages

    def init_client(self):
        self.client = OpenAI(
            api_key=self.key,
            base_url=self.base_url
        )

    def chat(self, user_message):
        """
        LLM 聊天接口
        """
        # 添加用户消息到历史记录
        self.messages.append(
            ChatCompletionUserMessageParam(content=user_message, role="user")
            )
        # 如果历史消息长度超过限制（不包括系统提示），删除最旧的消息
        while len(self.messages) > self.max_history + 1:
            # 删除第二条消息（保留系统提示，删除最旧的用户/助手消息）
            self.messages.pop(1)
        # 发起请求
        response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    stream=False)
        # 获取助手响应内容
        assistant_message = response.choices[0].message.content or ""
        # 将助手响应添加到历史记录
        self.messages.append(ChatCompletionAssistantMessageParam(
            content=assistant_message, role="assistant")
            )
        # 再次检查消息长度限制
        while len(self.messages) > self.max_history + 1:
            self.messages.pop(1)
        # 返回响应内容
        return assistant_message
    
    def save_messages(self):
        """保存当前会话的消息历史"""
        return save_messages_to_file(self.messages, self.group_id)
    
    def load_messages(self):
        """加载消息历史到当前会话"""
        return load_messages_from_file(self.group_id)
    
    def clear_history(self):
        """清除当前会话的消息历史，保留系统提示"""
        self.messages.clear()
        self.messages.append(ChatCompletionSystemMessageParam(content=self.prompt, role="system"))
