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

    async def save_memories_to_file(self) -> bool:
        """
        保存所有群的记忆到文件（每个群一个独立文件）
        返回：
            全部保存成功返回 True，任意一个失败返回 False
        """
        try:
            # 创建用户目录下的隐藏文件夹
            user_home = Path.home()
            hidden_dir = user_home / ".rmts_chat"
            hidden_dir.mkdir(exist_ok=True)
            
            all_success = True
            async with self._lock:
                # 遍历所有群
                for group_id, group_memories in self.memories.items():
                    try:
                        # 生成文件名
                        filename = f"rosmontis_memory_group_{group_id}.json"
                        filepath = hidden_dir / filename
                        
                        # 将记忆转换为可序列化的格式
                        serializable_data = {}
                        for doctor_id, memory_unit in group_memories.items():
                            serializable_data[doctor_id] = {
                                "max_length": memory_unit.max_length,
                                "memories": [mem.memory for mem in memory_unit.memory]
                            }
                        
                        # 使用异步文件写入
                        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                            await f.write(json.dumps(serializable_data, ensure_ascii=False, indent=2))
                        
                        logger.success(f"群 {group_id} 的记忆已保存到: {filepath}")
                    except Exception as e:
                        logger.error(f"保存群 {group_id} 的记忆失败: {e}")
                        all_success = False
            
            return all_success
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")
            return False

    async def load_memories_from_file(self) -> bool:
        """
        从文件加载所有群的记忆（扫描目录中所有记忆文件）
        返回：
            全部加载成功返回 True，任意一个失败返回 False
        """
        try:
            user_home = Path.home()
            hidden_dir = user_home / ".rmts_chat"
            
            if not hidden_dir.exists():
                logger.warning(f"记忆目录 {hidden_dir} 不存在")
                return False
            
            # 查找所有符合命名规则的记忆文件
            pattern = "rosmontis_memory_group_*.json"
            memory_files = list(hidden_dir.glob(pattern))
            
            if not memory_files:
                logger.warning(f"在 {hidden_dir} 中未找到记忆文件")
                return False
            
            all_success = True
            for filepath in memory_files:
                try:
                    # 从文件名提取群号
                    group_id = filepath.stem.replace("rosmontis_memory_group_", "")
                    
                    # 使用异步文件读取
                    async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        data = json.loads(content)
                    
                    async with self._lock:
                        # 重建记忆结构
                        if group_id not in self.memories:
                            self.memories[group_id] = {}
                        
                        for doctor_id, memory_data in data.items():
                            max_length = memory_data.get("max_length", self.max_length)
                            memory_unit = MemoryUnit(max_length)
                            
                            # 恢复记忆列表
                            for memory_content in memory_data.get("memories", []):
                                memory_unit.add_memory(Memory(memory_content))
                            
                            self.memories[group_id][doctor_id] = memory_unit
                    
                    logger.success(f"群 {group_id} 的记忆已从 {filepath} 加载")
                except Exception as e:
                    logger.error(f"加载文件 {filepath} 失败: {e}")
                    all_success = False
            
            return all_success
        except Exception as e:
            logger.error(f"加载记忆失败: {e}")
            return False
    