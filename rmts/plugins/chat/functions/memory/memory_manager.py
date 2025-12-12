import json
import aiofiles

from pathlib import Path
from typing import List, Dict

from nonebot.log import logger

class Memory:
    """
    单体记忆
    """

    def __init__(self, user_id: str) -> None:
        """
        初始化单体记忆
        参数：
            user_id: 用户的唯一标识符
        """
        self.user_id = user_id

        self.memory_data: Dict[str, str] = {}

    def add_memories(self, memories: Dict[str, str]) -> None:
        """
        添加记忆
        参数：
            memories: 记忆的键值对字典
        """
        self.memory_data.update(memories)

    def del_memories(self, keys: List[str]) -> None:
        """
        删除记忆
        参数：
            keys: 需要删除的记忆键列表
        """
        for key in keys:
            if key in self.memory_data:
                del self.memory_data[key]
    
    def get_memory(self, key: List[str]) -> Dict[str, str]:
        """
        获取记忆
        参数：
            keys: 需要获取的记忆键列表
        返回：
            记忆的键值对字典
        """
        return {key: self.memory_data[key] for key in key if key in self.memory_data}
    
    def get_all_keys(self) -> List[str]:
        """
        获取所有记忆键
        返回：
            所有记忆键的列表
        """
        return list(self.memory_data.keys())
    
    def to_dict(self) -> Dict:
        """
        将记忆对象转换为字典
        返回：
            记忆对象的字典表示
        """
        return {
            "user_id": self.user_id,
            "memory_data": self.memory_data
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
        memory = cls(data["user_id"])
        memory.memory_data = data["memory_data"]
        return memory

class GroupMemory:
    """
    单个群组记忆
    """

    def __init__(self, group_id: str) -> None:
        """
        初始化单个群组记忆
        """
        self.group_id = group_id
        self.user_memories: Dict[str, Memory] = {}
        self.group_golbal_memory: Memory = Memory(group_id) # 群组全局记忆

    def add_user_memories(self, user_id: str, memories: Dict[str, str]) -> None:
        """
        为指定用户添加记忆
        参数：
            user_id: 用户的唯一标识符
            memories: 记忆的键值对字典
        """
        if user_id not in self.user_memories:
            self.user_memories[user_id] = Memory(user_id)
        self.user_memories[user_id].add_memories(memories)

    def del_user_memories(self, user_id: str, keys: List[str]) -> None:
        """
        为指定用户删除记忆
        参数：
            user_id: 用户的唯一标识符
            keys: 需要删除的记忆键列表
        """
        if user_id in self.user_memories:
            self.user_memories[user_id].del_memories(keys)
    
    def get_user_memory(self, user_id: str, keys: List[str]) -> Dict[str, str]:
        """
        获取指定用户的记忆
        参数：
            user_id: 用户的唯一标识符
            keys: 需要获取的记忆键列表
        """
        if user_id in self.user_memories:
            return self.user_memories[user_id].get_memory(keys)
        return {}
    
    def get_user_all_keys(self, user_id: str) -> List[str]:
        """
        获取指定用户的所有记忆键
        参数：
            user_id: 用户的唯一标识符
        返回：
            用户所有记忆键的列表
        """
        if user_id in self.user_memories:
            return self.user_memories[user_id].get_all_keys()
        return []
    
    def to_dict(self) -> Dict:
        """
        将群组记忆对象转换为字典
        返回：
            群组记忆对象的字典表示
        """
        return {
            "group_id": self.group_id,
            "user_memories": {user_id: memory.to_dict() for user_id, memory in self.user_memories.items()},
            "group_global_memory": self.group_golbal_memory.to_dict()
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
        group_memory = cls(data["group_id"])
        group_memory.user_memories = {
            user_id: Memory.from_dict(memory_data) 
            for user_id, memory_data in data["user_memories"].items()
        }
        group_memory.group_golbal_memory = Memory.from_dict(data["group_global_memory"])
        return group_memory

class MemoryManager:
    """
    记忆管理类
    """

    def __init__(self) -> None:
        """
        初始化记忆管理类
        """
        self.group_memories: Dict[str, GroupMemory] = {}
        self.storage_dir = Path.home() / ".rmts_chat"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def add_memories(self, group_id: str, user_id: str, memories: Dict[str, str]) -> None:
        """
        为指定群组和用户添加记忆
        参数：
            group_id: 群组的唯一标识符
            user_id: 用户的唯一标识符
            memories: 记忆的键值对字典
        """
        if group_id not in self.group_memories:
            self.group_memories[group_id] = GroupMemory(group_id)
        self.group_memories[group_id].add_user_memories(user_id, memories)

    def del_memories(self, group_id: str, user_id: str, keys: List[str]) -> None:
        """
        为指定群组和用户删除记忆
        参数：
            group_id: 群组的唯一标识符
            user_id: 用户的唯一标识符
            keys: 需要删除的记忆键列表
        """
        if group_id in self.group_memories:
            self.group_memories[group_id].del_user_memories(user_id, keys)

    def get_memory(self, group_id: str, user_id: str, keys: List[str]) -> Dict[str, str]:
        """
        获取指定群组和用户的记忆
        参数：
            group_id: 群组的唯一标识符
            user_id: 用户的唯一标识符
            keys: 需要获取的记忆键列表
        """
        if group_id in self.group_memories:
            return self.group_memories[group_id].get_user_memory(user_id, keys)
        return {}
    
    def add_group_global_memories(self, group_id: str, memories: Dict[str, str]) -> None:
        """
        为指定群组添加全局记忆
        参数：
            group_id: 群组的唯一标识符
            memories: 记忆的键值对字典
        """
        if group_id not in self.group_memories:
            self.group_memories[group_id] = GroupMemory(group_id)
        self.group_memories[group_id].group_golbal_memory.add_memories(memories)

    def del_group_global_memories(self, group_id: str, keys: List[str]) -> None:
        """
        为指定群组删除全局记忆
        参数：
            group_id: 群组的唯一标识符
            keys: 需要删除的记忆键列表
        """
        if group_id in self.group_memories:
            self.group_memories[group_id].group_golbal_memory.del_memories(keys)

    def get_group_global_memory(self, group_id: str, keys: List[str]) -> Dict[str, str]:
        """
        获取指定群组的全局记忆
        参数：
            group_id: 群组的唯一标识符
            keys: 需要获取的记忆键列表
        """
        if group_id in self.group_memories:
            return self.group_memories[group_id].group_golbal_memory.get_memory(keys)
        return {}
    
    def get_user_all_keys(self, group_id: str, user_id: str) -> List[str]:
        """
        获取指定群组和用户的所有记忆键
        参数：
            group_id: 群组的唯一标识符
            user_id: 用户的唯一标识符
        返回：
            用户所有记忆键的列表
        """
        if group_id in self.group_memories:
            return self.group_memories[group_id].get_user_all_keys(user_id)
        return []
    
    def get_group_global_all_keys(self, group_id: str) -> List[str]:
        """
        获取指定群组的所有全局记忆键
        参数：
            group_id: 群组的唯一标识符
        返回：
            群组所有全局记忆键的列表
        """
        if group_id in self.group_memories:
            return self.group_memories[group_id].group_golbal_memory.get_all_keys()
        return []
    
    async def save_group_memory(self, group_id: str) -> bool:
        """
        异步保存指定群组的记忆到文件
        参数：
            group_id: 群组的唯一标识符
        返回：
            是否保存成功
        """
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
