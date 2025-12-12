import json
import aiofiles

from pathlib import Path
from typing import List, Dict
from collections import OrderedDict
from asyncio import Lock

from nonebot.log import logger

class Memory:
    """
    单体记忆
    """

    def __init__(self, user_id: str, max_memory_size: int = 100) -> None:
        """
        初始化单体记忆
        参数：
            user_id: 用户的唯一标识符
            max_memory_size: 记忆的最大字符数
        """
        self.user_id = user_id
        self.max_memory_size = max_memory_size

        self.memory_data: OrderedDict[str, str] = OrderedDict()

    def add_memories(self, memories: Dict[str, str]) -> None:
        """
        添加记忆
        参数：
            memories: 记忆的键值对字典（值为空时删除对应键）
        """
        # 处理记忆：空值删除，非空值添加/更新
        for key, value in memories.items():
            if not value or not value.strip():
                # 值为空或只有空白字符时删除该键
                self.memory_data.pop(key, None)
            else:
                # 添加或更新记忆
                self.memory_data[key] = value
        
        # 计算当前记忆的总字符数
        def calculate_total_chars() -> int:
            return sum(len(k) + len(v) for k, v in self.memory_data.items())
        
        # 如果超过限制，删除最旧的记忆
        while calculate_total_chars() > self.max_memory_size and len(self.memory_data) > 0:
            # 删除最旧的记忆（OrderedDict的第一个元素）
            self.memory_data.popitem(last=False)
    
    def to_dict(self) -> Dict:
        """
        将记忆对象转换为字典
        返回：
            记忆对象的字典表示
        """
        return {
            "user_id": self.user_id,
            "max_memory_size": self.max_memory_size,
            "memory_data": dict(self.memory_data)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Memory":
        """
        从字典创建记忆对象
        参数：
            data: 记忆对象的字典表示
        返回：
            Memory 对象
        """
        from collections import OrderedDict
        max_memory_size = data.get("max_memory_size", 100)
        memory = cls(data["user_id"], max_memory_size)
        memory.memory_data = OrderedDict(data["memory_data"])
        return memory

class GroupMemory:
    """
    单个群组记忆
    """

    def __init__(self, group_id: str, max_memory_size: int = 100) -> None:
        """
        初始化单个群组记忆
        """
        self.group_id = group_id
        self.max_memory_size = max_memory_size
        self.user_memories: Dict[str, Memory] = {}
        self.group_global_memory: Memory = Memory(group_id, max_memory_size) # 群组全局记忆

    def add_user_memories(self, user_id: str, memories: Dict[str, str]) -> None:
        """
        为指定用户添加记忆
        参数：
            user_id: 用户的唯一标识符
            memories: 记忆的键值对字典
        """
        if user_id not in self.user_memories:
            self.user_memories[user_id] = Memory(user_id, self.max_memory_size)
        self.user_memories[user_id].add_memories(memories)
    
    def get_user_all_memories(self, user_id: str) -> Dict[str, str]:
        """
        获取指定用户的所有记忆
        参数：
            user_id: 用户的唯一标识符
        返回：
            用户所有记忆的字典
        """
        if user_id in self.user_memories:
            return dict(self.user_memories[user_id].memory_data)
        return {}
    
    def to_dict(self) -> Dict:
        """
        将群组记忆对象转换为字典
        返回：
            群组记忆对象的字典表示
        """
        return {
            "group_id": self.group_id,
            "max_memory_size": self.max_memory_size,
            "user_memories": {user_id: memory.to_dict() for user_id, memory in self.user_memories.items()},
            "group_global_memory": self.group_global_memory.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "GroupMemory":
        """
        从字典创建群组记忆对象
        参数：
            data: 群组记忆对象的字典表示
        返回：
            GroupMemory 对象
        """
        max_memory_size = data.get("max_memory_size", 100)
        group_memory = cls(data["group_id"], max_memory_size)
        group_memory.user_memories = {
            user_id: Memory.from_dict(memory_data) 
            for user_id, memory_data in data["user_memories"].items()
        }
        group_memory.group_global_memory = Memory.from_dict(data["group_global_memory"])
        return group_memory

class MemoryManager:
    """
    记忆管理类
    """

    def __init__(self, max_memory_size: int = 100) -> None:
        """
        初始化记忆管理类
        参数：
            max_memory_size: 记忆的最大字符数
        """
        self.max_memory_size = max_memory_size
        self.group_memories: Dict[str, GroupMemory] = {}
        self.storage_dir = Path.home() / ".rmts_chat"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, Lock] = {}  # 每个群组的锁
    
    def _get_lock(self, group_id: str) -> Lock:
        """获取或创建指定群组的锁"""
        if group_id not in self._locks:
            self._locks[group_id] = Lock()
        return self._locks[group_id]

    async def add_memories(self, group_id: str, user_id: str, memories: Dict[str, str]) -> None:
        """
        为指定群组和用户添加记忆
        参数：
            group_id: 群组的唯一标识符
            user_id: 用户的唯一标识符
            memories: 记忆的键值对字典
        """
        async with self._get_lock(group_id):
            if group_id not in self.group_memories:
                self.group_memories[group_id] = GroupMemory(group_id, self.max_memory_size)
            self.group_memories[group_id].add_user_memories(user_id, memories)
    
    async def add_group_global_memories(self, group_id: str, memories: Dict[str, str]) -> None:
        """
        为指定群组添加全局记忆
        参数：
            group_id: 群组的唯一标识符
            memories: 记忆的键值对字典
        """
        async with self._get_lock(group_id):
            if group_id not in self.group_memories:
                self.group_memories[group_id] = GroupMemory(group_id, self.max_memory_size)
            self.group_memories[group_id].group_global_memory.add_memories(memories)
    
    async def get_user_all_memories(self, group_id: str, user_id: str) -> Dict[str, str]:
        """
        获取指定群组和用户的所有记忆
        参数：
            group_id: 群组的唯一标识符
            user_id: 用户的唯一标识符
        返回：
            用户所有记忆的字典
        """
        async with self._get_lock(group_id):
            if group_id in self.group_memories:
                return self.group_memories[group_id].get_user_all_memories(user_id)
            return {}
    
    async def get_group_global_all_memories(self, group_id: str) -> Dict[str, str]:
        """
        获取指定群组的所有全局记忆
        参数：
            group_id: 群组的唯一标识符
        返回：
            群组所有全局记忆的字典
        """
        async with self._get_lock(group_id):
            if group_id in self.group_memories:
                return dict(self.group_memories[group_id].group_global_memory.memory_data)
            return {}
    
    async def save_group_memory(self, group_id: str) -> bool:
        """
        异步保存指定群组的记忆到文件
        参数：
            group_id: 群组的唯一标识符
        返回：
            是否保存成功
        """
        async with self._get_lock(group_id):
            if group_id not in self.group_memories:
                logger.warning(f"群组 {group_id} 的记忆不存在，无法保存")
                return False
            
            try:
                file_path = self.storage_dir / f"rosmontis_memory_group_{group_id}.json"
                data = self.group_memories[group_id].to_dict()
                
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, ensure_ascii=False, indent=2))
                
                logger.info(f"成功保存群组 {group_id} 的记忆到 {file_path}")
                return True
            except Exception as e:
                logger.error(f"保存群组 {group_id} 的记忆时出错: {e}")
                return False
    
    async def load_group_memory(self, group_id: str) -> bool:
        """
        异步从文件加载指定群组的记忆
        参数：
            group_id: 群组的唯一标识符
        返回：
            是否加载成功
        """
        async with self._get_lock(group_id):
            try:
                file_path = self.storage_dir / f"rosmontis_memory_group_{group_id}.json"
                
                if not file_path.exists():
                    logger.warning(f"群组 {group_id} 的记忆文件不存在: {file_path}")
                    return False
                
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                
                self.group_memories[group_id] = GroupMemory.from_dict(data)
                logger.info(f"成功加载群组 {group_id} 的记忆，共 {len(self.group_memories[group_id].user_memories)} 个用户记忆")
                return True
            except Exception as e:
                logger.error(f"加载群组 {group_id} 的记忆时出错: {e}")
                return False
    
    async def save_all_memories(self) -> None:
        """
        异步保存所有群组的记忆
        """
        logger.info(f"开始保存所有群组记忆，共 {len(self.group_memories)} 个群组")
        for group_id in self.group_memories.keys():
            await self.save_group_memory(group_id)
        logger.info("所有群组记忆保存完成")
    
    async def load_all_memories(self) -> None:
        """
        异步加载所有已保存的群组记忆
        """
        logger.info(f"开始从 {self.storage_dir} 加载所有群组记忆")
        
        if not self.storage_dir.exists():
            logger.warning(f"存储目录不存在: {self.storage_dir}")
            return
        
        count = 0
        for file_path in self.storage_dir.glob("rosmontis_memory_group_*.json"):
            group_id = file_path.stem.replace("rosmontis_memory_group_", "")
            if await self.load_group_memory(group_id):
                count += 1
        
        logger.info(f"成功加载 {count} 个群组的记忆")
