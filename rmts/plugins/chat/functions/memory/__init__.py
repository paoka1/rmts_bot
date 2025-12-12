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
    description="在终端记下指定博士的信息"
)
func_desc_add_memories.add_dict_param(
    name="memories",
    description="信息的键值对字典，键和值都是字符串",
    value_type="string",
    required=True
)
func_desc_add_memories.add_injection_param(name="group_id", description="群组的唯一标识符")
func_desc_add_memories.add_injection_param(name="user_id", description="用户的唯一标识符")

@function_container.function_calling(func_desc_add_memories)
async def add_user_memories(memories: dict, group_id: str, user_id: str) -> str:
    mem_manager.add_memories(group_id, user_id, memories)
    await mem_manager.save_group_memory(group_id)
    keys = ", ".join(memories.keys())
    return f"已成功记下博士的信息：{keys}"

# 删除用户记忆
func_desc_del_memories = FunctionDescription(
    name="delete_user_memories",
    description="在终端删除指定博士的信息"
)
func_desc_del_memories.add_list_param(
    name="keys",
    description="需要删除的信息键列表",
    item_type="string",
    required=True
)
func_desc_del_memories.add_injection_param(name="group_id", description="群组的唯一标识符")
func_desc_del_memories.add_injection_param(name="user_id", description="用户的唯一标识符")

@function_container.function_calling(func_desc_del_memories)
async def delete_user_memories(keys: list, group_id: str, user_id: str) -> str:
    # 检查记忆是否存在
    existing_memories = mem_manager.get_memory(group_id, user_id, keys)
    
    if not existing_memories:
        return f"该博士没有这些信息：{', '.join(keys)}"
    
    non_existing_keys = [key for key in keys if key not in existing_memories]
    
    mem_manager.del_memories(group_id, user_id, keys)
    await mem_manager.save_group_memory(group_id)
    
    if non_existing_keys:
        deleted_keys = ", ".join(existing_memories.keys())
        missing_keys = ", ".join(non_existing_keys)
        return f"已删除信息：{deleted_keys}；但这些信息不存在：{missing_keys}"
    else:
        deleted_keys = ", ".join(keys)
        return f"已成功删除博士的信息：{deleted_keys}"

# 获取用户记忆
func_desc_get_memory = FunctionDescription(
    name="get_user_memories",
    description="在终端读取指定博士的信息"
)
func_desc_get_memory.add_list_param(
    name="keys",
    description="需要获取的信息键列表",
    item_type="string",
    required=True
)
func_desc_get_memory.add_injection_param(name="group_id", description="群组的唯一标识符")
func_desc_get_memory.add_injection_param(name="user_id", description="用户的唯一标识符")

@function_container.function_calling(func_desc_get_memory)
async def get_user_memories(keys: list, group_id: str, user_id: str) -> str:
    memories = mem_manager.get_memory(group_id, user_id, keys)
    
    if not memories:
        return f"博士没有这些信息：{', '.join(keys)}"
    
    non_existing_keys = [key for key in keys if key not in memories]
    
    result_lines = [f"{key}: {value}" for key, value in memories.items()]
    result = "\n".join(result_lines)
    
    if non_existing_keys:
        missing = ", ".join(non_existing_keys)
        return f"博士的信息：\n{result}\n\n但这些信息不存在：{missing}"
    else:
        return f"博士的信息：\n{result}"

# 添加群组全局记忆
func_desc_add_group_memories = FunctionDescription(
    name="add_group_global_memories",
    description="在终端记下全局信息"
)
func_desc_add_group_memories.add_dict_param(
    name="memories",
    description="信息的键值对字典，键和值都是字符串",
    value_type="string",
    required=True
)
func_desc_add_group_memories.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_add_group_memories)
async def add_group_global_memories(memories: dict, group_id: str) -> str:
    mem_manager.add_group_global_memories(group_id, memories)
    await mem_manager.save_group_memory(group_id)
    keys = ", ".join(memories.keys())
    return f"已成功记下全局信息：{keys}"

# 删除群组全局记忆
func_desc_del_group_memories = FunctionDescription(
    name="delete_group_global_memories",
    description="在终端删除全局信息"
)
func_desc_del_group_memories.add_list_param(
    name="keys",
    description="需要删除的信息键列表",
    item_type="string",
    required=True
)
func_desc_del_group_memories.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_del_group_memories)
async def delete_group_global_memories(keys: list, group_id: str) -> str:
    # 检查记忆是否存在
    existing_memories = mem_manager.get_group_global_memory(group_id, keys)
    
    if not existing_memories:
        return f"没有这些全局信息：{', '.join(keys)}"
    
    non_existing_keys = [key for key in keys if key not in existing_memories]
    
    mem_manager.del_group_global_memories(group_id, keys)
    await mem_manager.save_group_memory(group_id)
    
    if non_existing_keys:
        deleted_keys = ", ".join(existing_memories.keys())
        missing_keys = ", ".join(non_existing_keys)
        return f"已删除全局信息：{deleted_keys}；但这些信息不存在：{missing_keys}"
    else:
        deleted_keys = ", ".join(keys)
        return f"已成功删除全局信息：{deleted_keys}"

# 获取群组全局记忆
func_desc_get_group_memory = FunctionDescription(
    name="get_group_global_memories",
    description="在终端读取全局信息"
)
func_desc_get_group_memory.add_list_param(
    name="keys",
    description="需要获取的信息键列表",
    item_type="string",
    required=True
)
func_desc_get_group_memory.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_get_group_memory)
async def get_group_global_memories(keys: list, group_id: str) -> str:
    memories = mem_manager.get_group_global_memory(group_id, keys)
    
    if not memories:
        return f"没有这些全局信息：{', '.join(keys)}"
    
    non_existing_keys = [key for key in keys if key not in memories]
    
    result_lines = [f"{key}: {value}" for key, value in memories.items()]
    result = "\n".join(result_lines)
    
    if non_existing_keys:
        missing = ", ".join(non_existing_keys)
        return f"全局信息：\n{result}\n\n但这些信息不存在：{missing}"
    else:
        return f"全局信息：\n{result}"
