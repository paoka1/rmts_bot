"""
和交互动作有关的函数调用功能
"""

from nonebot import get_bot
from nonebot.adapters.onebot.v11 import MessageSegment

from rmts.plugins.chat.function_calling import FunctionDescription, function_container

# 戳一戳
func_desc_poke = FunctionDescription(name="poke_doctor", description="戳一戳指定博士")
func_desc_poke.add_param(name="doctor_id", description="博士的唯一标识符", param_type="integer", required=True)
func_desc_poke.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_poke)
async def poke_doctor(doctor_id: int, group_id: int) -> str:
    bot = get_bot()
    await bot.call_api(
        "send_poke",
        user_id=doctor_id,
        group_id=group_id
    )
    return f"你戳了戳ID为{doctor_id}的博士"

# 发送表情
from rmts.plugins.chat.functions.action.send_sticker import SendSticker

send_sticker_util = SendSticker()
func_desc_send_sticker = FunctionDescription(name="send_sticker",description="向博士发送指定表情")
func_desc_send_sticker.add_enum_param(name="type", description="表情类型", enum_values=send_sticker_util.get_sticker_list(), required=True)
func_desc_send_sticker.add_injection_param(name="group_id", description="群组的唯一标识符")

@function_container.function_calling(func_desc_send_sticker)
async def send_sticker(type: str, group_id: int) -> str:
    bot = get_bot()
    sticker_bytes = await send_sticker_util.get_sticker_bytes(type)
    if sticker_bytes is None:
        return f"表情 {type} 不存在"
    
    await bot.call_api(
        "send_group_msg",
        group_id=group_id,
        message=MessageSegment.image(file=sticker_bytes)
    )
    return f"已向博士发送表情 {type}"

# 群组禁言
func_desc_group_ban = FunctionDescription(name="group_ban", description="禁言指定博士一段时间")
func_desc_group_ban.add_param(name="doctor_id", description="博士的唯一标识符", param_type="integer", required=True)
func_desc_group_ban.add_param(name="duration", description="禁言持续时间，单位为秒", param_type="integer", required=True)

func_desc_group_ban.add_injection_param(name="group_id", description="群组的唯一标识符")
func_desc_group_ban.add_injection_param(name="user_id", description="用户的唯一标识符")

@function_container.function_calling(func_desc_group_ban)
async def group_ban(doctor_id: int, duration: int, group_id: int, user_id: int) -> str:
    bot = get_bot()

    if duration < 60:
        return "禁言持续时间必须大于60秒"
    
    if duration > 24 * 3600:
        return "禁言持续时间不能超过24小时"

    if doctor_id != user_id:
        return "博士只能对自己进行禁言，无法对其他博士进行禁言"
    
    await bot.call_api(
        "set_group_ban",
        group_id=group_id,
        user_id=doctor_id,
        duration=duration
    )
    return f"已对ID为{doctor_id}的博士进行禁言，持续时间为{duration}秒"
