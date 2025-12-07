"""
和交互动作有关的函数调用功能
"""
from nonebot import get_bot

from rmts.plugins.chat.function_calling import FunctionDescription, function_container

# 戳一戳
func_desc_poke = FunctionDescription(name="poke_user", description="戳一戳指定用户")
func_desc_poke.add_parameter(name="id", description="用户的唯一标识符", param_type="string")
func_desc_poke.add_injection_parameter(name="group_id", description="群组的唯一标识符")
func_desc_poke.add_return(name="result", description="操作结果")

@function_container.function_calling(func_desc_poke)
async def poke_user(id: int, group_id: int) -> str:
    bot = get_bot()
    await bot.call_api(
        "send_poke",
        user_id=id,
        group_id=group_id
    )
    return f"你戳了戳ID为{id}的用户"