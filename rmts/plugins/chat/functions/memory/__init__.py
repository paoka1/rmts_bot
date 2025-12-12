"""
和记忆相关的函数调用
"""

from nonebot import get_driver
from rmts.plugins.chat.function_calling import FunctionDescription, function_container

from .memory_manager import MemoryManager

# 记忆管理
mem_manager = MemoryManager()

# 加载和保存记忆
driver = get_driver()

@driver.on_startup
async def load_memories():
    """Bot 启动时加载所有记忆"""
    await mem_manager.load_all_memories()

@driver.on_shutdown
async def save_memories():
    """Bot 关闭时保存所有记忆"""
    await mem_manager.save_all_memories()

# 添加用户记忆
func_desc_add_memories = FunctionDescription(
    name="add_user_memories",
    description="在终端记下、删除或更改指定博士的信息"
)
func_desc_add_memories.add_dict_param(
    name="memories",
    description="信息的键值对字典，键和值都是字符串，值为空字符串表示删除该信息，值为'空'表示在值不存储信息",
    value_type="string",
    required=True
)
func_desc_add_memories.add_param(name="doctor_id", description="博士的唯一标识符", required=True)
func_desc_add_memories.add_injection_param(name="user_id", description="用户的唯一标识符")
func_desc_add_memories.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_add_memories)
async def add_user_memories(memories: dict, group_id: str, doctor_id: str, user_id: str) -> str:
    if user_id != doctor_id: # user_id: 触发函数的用户， doctor_id: AI 想要修改记忆的用户
        return f"id为{user_id}的博士想要修改id为{doctor_id}博士的信息，这是不允许的"
    await mem_manager.add_memories(group_id, doctor_id, memories)
    keys = ", ".join(memories.keys())
    return f"已成功记下博士的信息：{keys}"

# 获取用户所有记忆
func_desc_get_all_memories = FunctionDescription(
    name="get_user_all_memories",
    description="在终端读取指定博士的所有信息"
)
func_desc_get_all_memories.add_param(name="doctor_id", description="博士的唯一标识符", required=True)
func_desc_get_all_memories.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_get_all_memories)
async def get_user_all_memories(group_id: str, doctor_id: str) -> str:
    memories = await mem_manager.get_user_all_memories(group_id, doctor_id)
    
    if not memories:
        return "博士还没有任何记录的信息"
    
    result_lines = [f"{key}: {value}" for key, value in memories.items()]
    result = "\n".join(result_lines)
    return f"博士的所有信息：\n{result}"

# 添加群组全局记忆
func_desc_add_group_memories = FunctionDescription(
    name="add_group_global_memories",
    description="在终端记下、删除或更改全局信息"
)
func_desc_add_group_memories.add_dict_param(
    name="memories",
    description="信息的键值对字典，键和值都是字符串，值为空字符串表示删除该信息，值为'空'表示在值不存储信息",
    value_type="string",
    required=True
)
func_desc_add_group_memories.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_add_group_memories)
async def add_group_global_memories(memories: dict, group_id: str) -> str:
    await mem_manager.add_group_global_memories(group_id, memories)
    keys = ", ".join(memories.keys())
    return f"已成功记下全局信息：{keys}"

# 获取群组所有全局记忆
func_desc_get_group_all_memories = FunctionDescription(
    name="get_group_global_all_memories",
    description="在终端读取所有全局信息"
)
func_desc_get_group_all_memories.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_get_group_all_memories)
async def get_group_global_all_memories(group_id: str) -> str:
    memories = await mem_manager.get_group_global_all_memories(group_id)
    
    if not memories:
        return "还没有任何记录的全局信息"
    
    result_lines = [f"{key}: {value}" for key, value in memories.items()]
    result = "\n".join(result_lines)
    return f"所有全局信息：\n{result}"
