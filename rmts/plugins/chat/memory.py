from typing import Dict, List
from enum import Enum, auto

class MemoryType(Enum):
    """
    记忆类型
    """

    TEXT = auto() # 文字记忆
    IMAGE = auto() # 图片记忆
    VOICE = auto() # 语音记忆
    MIXED = auto() # 混合记忆

class Memory:
    """
    单个记忆
    """
    
    def __init__(self,
                 *,
                 group_id: int,
                 sender_id: int,
                 message_id: int,
                 sender_name: str,
                 memory_type: MemoryType,
                 content: Dict[MemoryType, str]):
        """
        参数：
            group_id: 群号
            sender_id: 发送者QQ号
            message_id: 消息ID
            sender_name: 发送者昵称
            memory_type: 记忆类型
            content: 记忆内容
        """
        self.group_id = group_id
        self.sender_id = sender_id
        self.message_id = message_id
        self.sender_name = sender_name
        self.memory_type = memory_type
        self.content = content
    
    def is_pure_text(self) -> bool:
        """
        是否为纯文字记忆
        """
        return self.memory_type == MemoryType.TEXT

class MemoryManager:
    """
    记忆管理
    """

    def __init__(self, group_id: int, max_memories: int = 100):
        """
        参数：
            group_id: 群号
            max_memories: 最大记忆条数
        """
        self.group_id = group_id
        self.max_memories = max_memories
        self.memories: List[Memory] = []

    def add_memory(self, memory: Memory) -> None:
        """
        添加记忆
        """
        if len(self.memories) >= self.max_memories:
            self.memories.pop(0) # 删除最早的记忆
        self.memories.append(memory)
    
    def clear_memories(self) -> None:
        """
        清除所有记忆
        """
        self.memories = []

    def delete_memory(self, message_id: int) -> bool:
        """
        删除指定记忆
        参数：
            message_id: 消息ID
        """
        for i, memory in enumerate(self.memories):
            if memory.message_id == message_id:
                self.memories.pop(i)
                return True
        return False
    
    def get_pure_text_memories(self) -> List[Memory]:
        """
        获取所有文字记忆，不包含混合记忆
        """
        return [m for m in self.memories if m.is_pure_text()]


class LongTermMemory(MemoryManager):
    """
    长期记忆
    """

    def __init__(self, group_id: int, max_memories: int = 1000):
        super().__init__(group_id, max_memories)


class ShortTermMemory(MemoryManager):
    """
    短期记忆
    """

    def __init__(self, group_id: int, max_memories: int = 100):
        super().__init__(group_id, max_memories)
