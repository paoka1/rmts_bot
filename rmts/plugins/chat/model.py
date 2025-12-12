import json

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam
from openai.types.chat import ChatCompletionUserMessageParam
from openai.types.chat import ChatCompletionAssistantMessageParam
from openai.types.chat import ChatCompletionToolMessageParam
from openai.types.chat import ChatCompletionMessageFunctionToolCall

from typing import List, Union, Optional

from .prompt import prompt
from .function_calling import FunctionCalling
from .history import save_messages_to_file, load_messages_from_file

class Model:
    """
    LLM 聊天模型封装类，方法：
        init_model: 初始化模型
        chat: 聊天接口
        save_messages: 保存消息历史
        load_messages: 加载消息历史
        clear_history: 清除消息历史
    说明：
        在调用 chat 方法前，需先调用 init_model 方法初始化模型
    """

    def __init__(self,
                 *,
                 group_id: int,
                 fc: FunctionCalling,
                 key: str,
                 base_url: str = "https://api.deepseek.com",
                 model: str = "deepseek-chat",
                 prompt: str = prompt,
                 max_history: int = 10
    ) -> None:
        """
        参数：
            group_id: 群号
            fc: 函数调用管理器
            key: deepseek API 密钥
            base_url: API 基础 URL
            model: 使用的模型名称
            prompt: 系统提示语
            max_history: 最大历史消息条数
        """

        self.client: AsyncOpenAI
        self.group_id = group_id
        self.fc = fc
        self.key = key
        self.base_url = base_url
        self.model = model
        self.prompt = prompt
        self.max_history = max_history
        self.messages: List[Union[ChatCompletionSystemMessageParam,
                                  ChatCompletionUserMessageParam,
                                  ChatCompletionAssistantMessageParam,
                                  ChatCompletionToolMessageParam]] = []

    async def init_model(self) -> None:
        """
        初始化 OpneAI 客户端，加载历史消息
        """
        self.client = AsyncOpenAI(
            api_key=self.key,
            base_url=self.base_url
        )

        # 读取历史消息
        messages = await self.load_messages()
        if messages == []:
            # 初始化历史消息列表，包含系统提示
            self.messages.append(ChatCompletionSystemMessageParam(content=self.prompt, role="system"))
        else:
            self.messages = messages

    async def chat(self, user_message: str) -> Optional[str]:
        """
        LLM 聊天接口
        """

        # 添加用户消息到历史记录
        self.messages.append(ChatCompletionUserMessageParam(content=user_message, role="user"))
        
        # 如果历史消息长度超过限制（不包括系统提示），删除最旧的消息
        if len(self.messages) > self.max_history + 1:
            # 保留系统提示（第一条）和最新的 max_history 条消息
            self.messages = [self.messages[0]] + self.messages[-(self.max_history):]

        # 发起请求
        response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=1.5,
                    tools=self.fc.to_schemas(),
                    tool_choice="auto",
                    stream=False)
        # 获取响应内容
        response_message = response.choices[0].message

        # 检查是否有工具调用
        if response_message.tool_calls:
            self.messages.append(ChatCompletionAssistantMessageParam(
                role="assistant",
                content=response_message.content,
                tool_calls=[
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in response_message.tool_calls
                    if isinstance(tool_call, ChatCompletionMessageFunctionToolCall)
                ]
            ))

            # 执行所有函数调用
            for tool_call in response_message.tool_calls:
                if not isinstance(tool_call, ChatCompletionMessageFunctionToolCall):
                    continue

                function_name = tool_call.function.name
                function_args = tool_call.function.arguments

                try:
                    args_dict = json.loads(function_args)
                    # 调用函数并获取结果
                    function_response = await self.fc.call(function_name, args_dict)
                except json.JSONDecodeError:
                    function_response = f"函数参数解析错误: {function_args}"

                # 添加工具返回结果
                self.messages.append(ChatCompletionToolMessageParam(
                    role="tool",
                    tool_call_id=tool_call.id,
                    content=function_response
                ))
            
            # 再次调用聊天接口，获取最终响应
            call_again_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=1.5,
                    tools=self.fc.to_schemas(),
                    tool_choice="auto",
                    stream=False)
            response_message = call_again_response.choices[0].message

        else: # 没有工具调用，直接使用助手响应
            response_message = response.choices[0].message

        # 将助手响应添加到历史记录
        self.messages.append(ChatCompletionAssistantMessageParam(content=response_message.content, role="assistant"))

        # 返回响应内容
        return response_message.content
    
    async def save_messages(self):
        """保存当前会话的消息历史"""
        return await save_messages_to_file(self.messages, self.group_id)
    
    async def load_messages(self):
        """加载消息历史到当前会话"""
        return await load_messages_from_file(self.group_id)
    
    def clear_history(self):
        """清除当前会话的消息历史，保留系统提示"""
        self.messages.clear()
        self.messages.append(ChatCompletionSystemMessageParam(content=self.prompt, role="system"))
