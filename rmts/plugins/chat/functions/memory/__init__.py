"""
和记忆或信息存储相关的函数调用
"""

from nonebot import get_driver
from rmts.plugins.chat.function_calling import FunctionDescription, function_container

from .memory_manager import MemoryManager, Memory

# 记忆管理
mem_manager = MemoryManager()
# 加载和保存记忆
driver = get_driver()

# Bot 启动时加载所有记忆
@driver.on_startup
async def load_memories():
    await mem_manager.load_memories_from_file()

# Bot 关闭时保存所有记忆
@driver.on_shutdown
async def save_memories():
    await mem_manager.save_memories_to_file()

# 添加用户记忆
func_desc_add_info = FunctionDescription("add_user_info", "在终端添加指定博士的信息")
func_desc_add_info.add_list_param("info", "信息的列表", "string", True)
func_desc_add_info.add_param(name="doctor_id", description="博士的唯一标识符", param_type="integer", required=True)
func_desc_add_info.add_injection_param(name="user_id", description="用户的唯一标识符")
func_desc_add_info.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_add_info)
async def add_user_info(info: list, group_id: int, doctor_id: int, user_id: int) -> str:
    # user_id: 触发函数的用户， doctor_id: AI 想要修改记忆的用户
    # 只允许用户对自己的信息的修改
    if user_id != doctor_id:
        return f"ID为{user_id}的博士想要修改ID为{doctor_id}博士的信息，这是不可以的"
    await mem_manager.add_memories(str(group_id), str(doctor_id), [Memory(m) for m in info])
    return f"已成功记下博士的信息"

# 获取用户所有记忆
func_desc_get_all_info = FunctionDescription("get_user_all_info", "在终端读取指定博士的所有信息")
func_desc_get_all_info.add_param(name="doctor_id", description="博士的唯一标识符", param_type="integer", required=True)
func_desc_get_all_info.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_get_all_info)
async def get_user_all_info(group_id: int, doctor_id: int) -> str:
    memories = await mem_manager.get_user_memories(str(group_id), str(doctor_id))
    if not memories:
        return "博士还没有任何记录的信息"
    return f"博士的所有信息：\n{memories.get_all_memory()}"

# 添加群组全局记忆
func_desc_add_group_info = FunctionDescription("add_group_global_info", "在终端添加全局信息")
func_desc_add_group_info.add_list_param("info", "信息的列表", "string", True)
func_desc_add_group_info.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_add_group_info)
async def add_group_global_info(info: list, group_id: int) -> str:
    await mem_manager.add_memories(str(group_id), str(group_id), [Memory(m) for m in info])
    return f"已成功记下全局信息"

# 获取群组所有全局记忆
func_desc_get_group_all_info = FunctionDescription("get_group_global_all_info", "在终端读取所有全局信息")
func_desc_get_group_all_info.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_get_group_all_info)
async def get_group_global_all_info(group_id: int) -> str:
    memories = await mem_manager.get_user_memories(str(group_id), str(group_id))
    if not memories:
        return "还没有任何记录的全局信息"
    return f"群组的所有全局信息：\n{memories.get_all_memory()}"
