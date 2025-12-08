"""
和交互动作有关的函数调用功能
"""
from nonebot import get_bot

from rmts.plugins.chat.function_calling import FunctionDescription, function_container

# 戳一戳
func_desc_poke = FunctionDescription(name="poke_doctor", description="戳一戳指定博士")
func_desc_poke.add_str_parameter(name="id", description="博士的唯一标识符", param_type="string", required=True)
func_desc_poke.add_injection_parameter(name="group_id", description="群组的唯一标识符")
func_desc_poke.add_return(name="result", description="操作结果")

@function_container.function_calling(func_desc_poke)
async def poke_doctor(id: int, group_id: int) -> str:
    bot = get_bot()
    await bot.call_api(
        "send_poke",
        user_id=id,
        group_id=group_id
    )
    return f"你戳了戳ID为{id}的博士"

# 发送表情包
from rmts.plugins.chat.functions.action.send_sticker import SendSticker

send_sticker_util = SendSticker()
func_desc_send_sticker = FunctionDescription(name="send_sticker",description="发送指定表情包")
func_desc_send_sticker.add_enum_parameter(name="type", description="表情包类型", enum_values=send_sticker_util.get_sticker_list(), required=True)
func_desc_send_sticker.add_injection_parameter(name="group_id", description="群组的唯一标识符")
func_desc_send_sticker.add_return(name="result", description="操作结果")

@function_container.function_calling(func_desc_send_sticker)
async def send_sticker(type: str, group_id: int) -> str:
    bot = get_bot()
    sticker_path = send_sticker_util.get_sticker_path(type)
    if sticker_path is None:
        return f"表情包 {type} 不存在"
    
    await bot.call_api(
        "send_group_msg",
        group_id=group_id,
        message={"type": "image", "data": {"file": "file://" + str(sticker_path)}}
    )
    return f"已发送表情包 {type}"
