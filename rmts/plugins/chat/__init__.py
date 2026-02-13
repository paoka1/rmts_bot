import random

from nonebot import logger
from nonebot import get_driver
from nonebot.rule import is_type
from nonebot import on_message, on_notice, on_fullmatch
from nonebot.rule import to_me, Rule
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11 import Bot, PokeNotifyEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from rmts.utils.nonebot import is_poke_me
from rmts.utils.nonebot import get_nickname
from rmts.utils import acquire_global_token_decorator as acquire_token

from .pool import ModelPool
from .clear_history import ClearHistory
from .function_calling import function_container

# 初始化聊天池
model_pool = ModelPool(function_container)

# 艾特机器人时触发的聊天响应器
chat = on_message(rule=to_me() & is_type(GroupMessageEvent), priority=5)

@chat.handle()
@acquire_token()
async def rmts_chat(bot: Bot, event: GroupMessageEvent):
    # 提取当前消息中的图片
    images = [seg.data.get("url") for seg in event.get_message() if seg.type == "image"]
    
    # 检查是否有回复消息
    reply_msg = None
    for seg in event.get_message():
        if seg.type == "reply" and (reply_msg_id := seg.data.get("id")):
            try:
                # 获取被回复消息的详细信息
                reply_msg = await bot.get_msg(message_id=int(reply_msg_id))
                break
            except Exception as e:
                logger.warning(f"获取被回复消息失败: {e}")
                await chat.finish()  # 无法获取被回复消息，结束处理
    
    # 如果有被回复的消息，提取其中的图片
    if reply_msg:
        replied_message = Message(reply_msg.get("message"))
        replied_images = [seg.data.get("url") for seg in replied_message if seg.type == "image"]
        # 将被回复消息中的图片添加到图片列表
        images.extend(replied_images)
    
    if len(images) > 1:
        logger.warning(f"群聊{event.group_id}中用户{event.user_id}发送了多张图片{images}，已忽略")
        await chat.finish()

    text = event.get_plaintext().strip()
    if len(text) > 325:
        logger.warning(f"群聊{event.group_id}中用户{event.user_id}发送过长消息{text}，长度为{len(text)}，已忽略")
        await chat.finish()

    nickname = event.sender.card if event.sender.card else event.sender.nickname
    user_message = f"博士（TA的名字是：{nickname}，TA的ID是{event.user_id}）"
    if images:
        images_text = "，".join(f"第{i+1}张图片的链接是：{url}" for i, url in enumerate(images))
        user_message += f"，发送了图片：{images_text}"
    user_message += f"，对你说：{text}"
    reply = await model_pool.chat(event.group_id, event.user_id, user_message)
    if reply:
        await chat.finish(MessageSegment.reply(event.message_id) + f"{reply}")


poke_msgs = ["博士（TA的名字是：{}，TA的ID是{}）戳了戳你",
             "博士（TA的名字是：{}，TA的ID是{}）轻轻地戳了戳你",
             "博士（TA的名字是：{}，TA的ID是{}）拍了拍你",
             "博士（TA的名字是：{}，TA的ID是{}）向你打招呼",
             "博士（TA的名字是：{}，TA的ID是{}）摸了摸你",
             "你看见了博士（TA的名字是：{}，TA的ID是{}）"]

# 使用自定义 rule 创建事件响应器
poke_handler = on_notice(rule=Rule(is_poke_me), priority=3, block=True)

@poke_handler.handle()
@acquire_token()
async def handle_poke(bot: Bot, event: PokeNotifyEvent):
    if event.group_id is None: # 私聊戳一戳不回复
        await poke_handler.finish()

    nickname = await get_nickname(bot, event.group_id, event.user_id)
    text = random.choice(poke_msgs).format(nickname, event.user_id)

    reply = await model_pool.chat(event.group_id, event.user_id, text)
    if reply:
        await poke_handler.finish(MessageSegment.at(event.user_id) + f" {reply}")


# 在程序关闭时保存聊天记录
driver = get_driver()

@driver.on_shutdown
async def save_chat_history():
    await model_pool.save_messages()


# 记忆清除
config = get_driver().config
history_clearer = ClearHistory(model_pool, config.clear_history_available_groups)

clear_history_handler = on_fullmatch("清除记忆", rule=to_me() & is_type(GroupMessageEvent), priority=2, block=True)

@clear_history_handler.handle()
@acquire_token()
async def handle_clear_history(event: GroupMessageEvent): 
    reply = await history_clearer.try_clear(event.group_id, event.user_id)
    await clear_history_handler.finish(MessageSegment.reply(event.message_id) + f"{reply}")
