import random

from nonebot import on_keyword
from nonebot.rule import is_type
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from rmts.utils import acquire_global_token_decorator as acquire_token

# 关键词与对应的表情包ID
emoji_like_rule = {
    frozenset({"新年快乐"}): [333],
    frozenset({"生日快乐"}): [53],
    frozenset({"面包"}): [12783]
}

emoji_like = on_keyword(
    set().union(*emoji_like_rule.keys()),
    priority=2,
    rule=is_type(GroupMessageEvent),
    block=False
)

@emoji_like.handle()
@acquire_token()
async def handle_emoji_like(bot: Bot, event: GroupMessageEvent):
    message_text = event.get_message().extract_plain_text()

    for keywords, emoji_ids in emoji_like_rule.items():
        if any(keyword in message_text for keyword in keywords):
            emoji_id = random.choice(emoji_ids)
            await bot.call_api(
                "set_msg_emoji_like",
                message_id=event.message_id,
                emoji_id=emoji_id
            )
            await emoji_like.finish()
