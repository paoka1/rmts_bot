from nonebot import get_driver

from .model import Model
from .function_calling import FunctionContainer
from .function_calling import FunctionCalling

class ModelPool:
    """
    创建和管理不同群的 Model 实例
    """

    def __init__(self, function_container: FunctionContainer):
        """
        参数：
            function_container: 全局唯一的函数容器
        """

        self.function_container = function_container
        self.pool: dict[int, Model] = {}
        self.key = get_driver().config.api_key
        self.base_url = get_driver().config.base_url
        self.model = get_driver().config.model_name
        self.max_history_length = get_driver().config.max_history_length

    def chat(self, group_id: int, user_message: str) -> str:
        """
        参数：
            group_id: 群号
            user_message: 用户发送的消息
        """
        if group_id not in self.pool:
            model = Model(group_id=group_id,
                          fc=FunctionCalling(self.function_container),
                          key=self.key,
                          base_url=self.base_url,
                          model=self.model,
                          max_history=self.max_history_length)
            model.init_client()
            self.pool[group_id] = model
        return self.pool[group_id].chat(user_message)

    def clear_history(self, group_id: int):
        """
        参数：
            group_id: 群号
        """
        if group_id in self.pool:
            self.pool[group_id].clear_history()

    def save_messages(self):
        for model in self.pool.values():
            model.save_messages()
