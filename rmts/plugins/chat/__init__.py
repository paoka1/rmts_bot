import random

from nonebot import get_driver
from nonebot.rule import is_type
from nonebot import on_message, on_notice, on_fullmatch
from nonebot.rule import to_me, Rule
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11 import Bot, PokeNotifyEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from rmts.utils.rule import is_poke_me
from rmts.utils.info import get_nickname

from .pool import ModelPool
from .clear_history import ClearHistory

# 初始化聊天池
model_pool = ModelPool()

# 艾特机器人时触发的聊天响应器
chat = on_message(rule=to_me() & is_type(GroupMessageEvent), priority=5)

@chat.handle()
async def rmts_chat(event: GroupMessageEvent):
    text = event.get_plaintext().strip()
    nickname = event.sender.card if event.sender.card else event.sender.nickname
    reply = model_pool.chat(event.group_id, f"博士（TA的名字是：{nickname}）对你说：" + text)
    await chat.finish(MessageSegment.reply(event.message_id) + f"{reply}")


poke_msgs = ["博士（TA的名字是：{}）戳了戳你",
             "博士（TA的名字是：{}）轻轻地戳了戳你",
             "博士（TA的名字是：{}）拍了拍你",
             "博士（TA的名字是：{}）向你打招呼",
             "博士（TA的名字是：{}）摸了摸你",
             "你看见了博士（TA的名字是：{}）"]

# 使用自定义 rule 创建事件响应器
poke_handler = on_notice(rule=Rule(is_poke_me), priority=3, block=True)

@poke_handler.handle()
async def handle_poke(bot: Bot, event: PokeNotifyEvent):
    nickname = await get_nickname(bot, event.group_id, event.user_id)
    text = random.choice(poke_msgs).format(nickname)
    if event.group_id is None: # 私聊戳一戳不回复
        await poke_handler.finish()
    reply = model_pool.chat(event.group_id, text)
    await poke_handler.send(MessageSegment.at(event.user_id) + f" {reply}")


# 在程序关闭时保存聊天记录
driver = get_driver()

@driver.on_shutdown
async def save_chat_history():
    model_pool.save_messages()


# 记忆清除
config = get_driver().config
history_clearer = ClearHistory(model_pool, config.clear_history_available_groups)

clear_history_handler = on_fullmatch("清除记忆", rule=to_me() & is_type(GroupMessageEvent), priority=2, block=True)

@clear_history_handler.handle()
async def handle_clear_history(event: GroupMessageEvent):
    group_id = event.group_id
    sender_id = event.user_id
    reply = history_clearer.try_clear(group_id, sender_id)
    await clear_history_handler.finish(MessageSegment.reply(event.message_id) + f"{reply}")
