from nonebot.adapters.onebot.v11 import Bot
from typing import Optional

async def get_nickname(bot: Bot, group_id: Optional[int], user_id: int) -> str:
    """
    获取用户在群里的昵称（优先群名片，fallback QQ 昵称）

    :param bot: 当前 Bot 对象
    :param group_id: 群号
    :param user_id: 用户 QQ
    :return: 群昵称（群名片或 QQ 昵称）
    """
    if group_id is not None:
        info = await bot.get_group_member_info(
            group_id=group_id,
            user_id=user_id
        )
        return str(info.get("card") or info.get("nickname"))
    else:
        info = await bot.get_stranger_info(user_id=user_id)
        return str(info.get("nickname"))
