from nonebot import get_driver
from nonebot import on_message, on_notice
from nonebot.rule import to_me, Rule
from nonebot.adapters.onebot.v11 import MessageSegment, MessageEvent
from nonebot.adapters.onebot.v11 import Bot, PokeNotifyEvent

from rmts.utils.rule import is_poke_me
from rmts.utils.info import get_nickname

from .deepseek import RMTSPlugin

# 初始化 deepseek 客户端
rmts = RMTSPlugin(max_history=100)
rmts.init_client()

# 艾特机器人时触发的聊天响应器
chat = on_message(rule=to_me(), priority=5)

@chat.handle()
async def rmts_chat(event: MessageEvent):
    text = event.get_plaintext().strip()
    nickname = event.sender.card if event.sender.card else event.sender.nickname
    message_id = event.message_id
    reply = rmts.chat(f"博士（TA的名字是：{nickname}）对你说：" + text)
    await chat.finish(
        MessageSegment.reply(message_id) + f"{reply}"
    )

# 使用自定义 rule 创建事件响应器
poke_handler = on_notice(rule=Rule(is_poke_me), priority=3, block=True)

@poke_handler.handle()
async def handle_poke(bot: Bot, event: PokeNotifyEvent):
    nickname = await get_nickname(bot, event.group_id, event.user_id)
    text = f"博士（TA的名字是：{nickname}）戳了戳你"
    reply = rmts.chat(text)
    await poke_handler.send(MessageSegment.at(event.user_id) + f" {reply}")

# 在程序关闭时保存聊天记录
driver = get_driver()

@driver.on_shutdown
async def save_chat_history():
    rmts.save_messages()
