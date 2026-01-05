import json
import aiofiles

from pathlib import Path
from asyncio import Lock
from typing import List, Dict, Optional

from nonebot.log import logger

class Memory:
    """
    单个记忆
    """

    def __init__(self, memory: str) -> None:
        """
        参数：
            memory: 记忆内容
        """
        self.memory = memory

    def get_length(self) -> int:
        """
        获取记忆内容的长度
        """
        return len(self.memory)

class MemoryUnit:
    """
    记忆单元
    """

    def __init__(self, max_length: int) -> None:
        """
        参数：
            max_length: 记忆最大长度
        """
        self.max_length = max_length
        self.memory: List[Memory] = [] # 记忆列表
    
    def add_memory(self, memory: Memory) -> None:
        """
        添加记忆：
        参数：
            memory: 记忆内容
        """
        self.memory.append(memory)
        # 确保记忆总长度不超过最大长度
        while (sum(mem.get_length() for mem in self.memory) > self.max_length) and self.memory:
            self.memory.pop(0)

    def get_all_memory(self) -> str:
        """
        获取所有记忆内容的拼接字符串
        """
        return "\n".join(mem.memory for mem in self.memory)

class MemoryManager:
    """
    记忆管理器
    """

    def __init__(self, max_length: int = 300) -> None:
        """
        参数：
            max_length: 每个记忆单元的最大长度
        """
        self.max_length = max_length
        self.memories: Dict[str, Dict[str, MemoryUnit]] = {} # 群号 -> id -> 记忆
        self._lock = Lock()  # 并发安全锁

    async def add_memories(self, group_id: str, doctor_id: str, memories: List[Memory]) -> None:
        """
        添加记忆：
        参数：
            group_id: 群号
            doctor_id: 博士ID
            memories: 记忆列表
        """
        async with self._lock:
            if group_id not in self.memories:
                self.memories[group_id] = {}

            if doctor_id not in self.memories[group_id]:
                self.memories[group_id][doctor_id] = MemoryUnit(self.max_length)
            
            for memory in memories:
                self.memories[group_id][doctor_id].add_memory(memory)

    async def get_user_memories(self, group_id: str, doctor_id: str) -> Optional[MemoryUnit]:
        """
        获取用户所有记忆：
        参数：
            group_id: 群号
            doctor_id: 博士ID
        返回：
            所有记忆内容
        """
        async with self._lock:
            if group_id in self.memories and doctor_id in self.memories[group_id]:
                return self.memories[group_id][doctor_id]
            
            return None
    