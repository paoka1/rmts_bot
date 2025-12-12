import asyncio
from typing import Optional
from nonebot import get_driver

from .model import Model
from .function_calling import FunctionContainer
from .function_calling import FunctionCalling
from .history import delete_messages_file

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
        self.locks: dict[int, asyncio.Lock] = {}  # 每个群组一个锁
        self.key = get_driver().config.api_key
        self.base_url = get_driver().config.base_url
        self.model = get_driver().config.model_name
        self.max_history_length = get_driver().config.max_history_length

    async def chat(self, group_id: int, user_id:int, user_message: str) -> Optional[str]:
        """
        参数：
            group_id: 群号
            user_id: 用户 ID
            user_message: 用户发送的消息
        """
        # 确保该群组有对应的锁
        if group_id not in self.locks:
            self.locks[group_id] = asyncio.Lock()
        
        # 使用锁确保同一群组的消息顺序处理
        async with self.locks[group_id]:
            if group_id not in self.pool: # 懒加载
                injection_params = {"group_id": str(group_id)} # 注入参数，在 Model 中也会动态注入参数
                function_calling = FunctionCalling(self.function_container, injection_params)

                model = Model(group_id=group_id,
                              fc=function_calling,
                              key=self.key,
                              base_url=self.base_url,
                              model=self.model,
                              max_history=self.max_history_length)
                await model.init_model()
                self.pool[group_id] = model
            return await self.pool[group_id].chat(user_message, user_id)

    async def clear_history(self, group_id: int):
        """
        参数：
            group_id: 群号
        """
        if group_id not in self.locks:
            self.locks[group_id] = asyncio.Lock()
        
        async with self.locks[group_id]:
            if group_id in self.pool:
                # Model 已加载,清空内存中的历史记录
                self.pool[group_id].clear_history()
            else:
                # Model 未加载,直接删除磁盘文件
                delete_messages_file(group_id)

    async def save_messages(self):
        """
        保存所有群组的消息历史
        """
        # 为所有群组的保存操作加锁
        for group_id, model in self.pool.items():
            if group_id not in self.locks:
                self.locks[group_id] = asyncio.Lock()
            async with self.locks[group_id]:
                await model.save_messages()
