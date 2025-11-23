from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent

from .deepseek import RMTSPlugin

rmts = RMTSPlugin()
rmts.init_client()

chat = on_message(rule=to_me(), priority=1)

@chat.handle()
async def rmts_chat(event: MessageEvent):
    text = event.get_plaintext().strip()
    message_id = event.message_id
    reply = rmts.chat(text)
    await chat.finish(
        MessageSegment.reply(message_id) + f"{reply}"
    )
