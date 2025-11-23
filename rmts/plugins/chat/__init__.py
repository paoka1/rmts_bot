from nonebot import on_message, on_notice
from nonebot.rule import to_me, Rule
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent
from nonebot.adapters.onebot.v11 import Bot, Event, PokeNotifyEvent

from .deepseek import RMTSPlugin

# 初始化 deepseek 客户端
rmts = RMTSPlugin()
rmts.init_client()

# 艾特机器人时触发的聊天响应器
chat = on_message(rule=to_me(), priority=5)

@chat.handle()
async def rmts_chat(event: MessageEvent):
    text = event.get_plaintext().strip()
    message_id = event.message_id
    reply = rmts.chat(text)
    await chat.finish(
        MessageSegment.reply(message_id) + f"{reply}"
    )

# 自定义 Rule：判断是否是戳到bot的poke事件
async def is_poke_me(event: Event) -> bool:
    return isinstance(event, PokeNotifyEvent) and event.is_tome()

# 使用自定义 rule 创建事件响应器
poke_handler = on_notice(rule=Rule(is_poke_me), priority=3, block=True)

@poke_handler.handle()
async def handle_poke(bot: Bot, event: PokeNotifyEvent):
    text = "博士戳了戳你"
    reply = rmts.chat(text)
    await poke_handler.send(MessageSegment.at(event.user_id) + f" {reply}")
