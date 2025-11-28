from nonebot.rule import is_type, to_me
from nonebot.adapters.onebot.v11 import Bot
from nonebot import on_keyword, on_fullmatch
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .weishu import WeiShu

# 关键词判定
weishu_wait = WeiShu()

weishu_invite_matcher = on_keyword(set(["邀请你加入卫戍协议:盟约【"]), rule=is_type(GroupMessageEvent), priority=2, block=True)

@weishu_invite_matcher.handle()
async def handle_invite(bot: Bot, event: GroupMessageEvent):
    message_id = event.message_id

    if weishu_wait.get_all(event.group_id) == []:
        message = MessageSegment.reply(message_id) + "我也要和博士一起玩卫戍协议"
    else:
        wait_list = weishu_wait.get_all(event.group_id)
        weishu_wait.remove_all(event.group_id)
        message = MessageSegment.reply(message_id)
        for user_id in wait_list:
            message += MessageSegment.at(user_id)

    await weishu_invite_matcher.finish(message)


# 预约判定
weishu_wait_matcher = on_fullmatch("预约卫戍", rule=to_me() & is_type(GroupMessageEvent), priority=2, block=True)

@weishu_wait_matcher.handle()
async def handle_wait(event: GroupMessageEvent):
    result = weishu_wait.add_wait(event.group_id, event.user_id)
    await weishu_wait_matcher.finish(result)
