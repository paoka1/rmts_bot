from nonebot import get_driver

from .deepseek import RMTSPlugin

class RMTSPool:
    """
    创建和管理不同群的 RMTSPlugin 实例
    """

    def __init__(self):
        self.pool: dict[int, RMTSPlugin] = {}
        self.key = get_driver().config.deepseek_api_key

    def chat(self, group_id: int, user_message: str) -> str:
        """
        参数：
            group_id: 群号
            user_message: 用户发送的消息
        """
        if group_id not in self.pool:
            rmts = RMTSPlugin(group_id, self.key, max_history=100)
            rmts.init_client()
            self.pool[group_id] = rmts
        return self.pool[group_id].chat(user_message)

    def clear_history(self, group_id: int):
        """
        参数：
            group_id: 群号
        """
        if group_id in self.pool:
            self.pool[group_id].clear_history()

    def save_messages(self):
        for rmts in self.pool.values():
            rmts.save_messages()
