from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11 import Bot, MessageEvent

keywords = set(["邀请你加入卫戍协议:盟约【"])
wsxy_invite_matcher = on_keyword(keywords, priority=2, block=True)

@wsxy_invite_matcher.handle()
async def handle_invite(bot: Bot, event: MessageEvent):
    message_id = event.message_id
    await wsxy_invite_matcher.finish(
        MessageSegment.reply(message_id) + "我也要和博士一起玩卫戍协议"
    )
