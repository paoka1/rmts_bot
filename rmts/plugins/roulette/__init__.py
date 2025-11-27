"""
灵感来源：https://github.com/PallasBot/Pallas-Bot
"""

from nonebot import get_driver
from nonebot.rule import is_type, to_me
from nonebot.adapters.onebot.v11 import Bot
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .game import RouletteGame

config = get_driver().config

roulette_game = RouletteGame(config.roulette_available_groups, misfire_prob=0.05)

roulette_game_handler = on_fullmatch("香香轮盘", rule=to_me() & is_type(GroupMessageEvent), priority=2, block=True)

@roulette_game_handler.handle()
async def handle_roulette_game(bot: Bot, event: GroupMessageEvent):
    await roulette_game_handler.finish(
        MessageSegment.reply(event.message_id) + roulette_game.start(event.group_id))


roulette_spin_handler = on_fullmatch("香香开枪", rule=to_me() & is_type(GroupMessageEvent), priority=2, block=True)

@roulette_spin_handler.handle()
async def handle_roulette_spin(bot: Bot, event: GroupMessageEvent):
    text, is_fire = roulette_game.fire(event.group_id)
    await roulette_spin_handler.send(MessageSegment.reply(event.message_id) + text)
    if is_fire:
        await bot.set_group_ban(
            group_id=event.group_id,
            user_id=event.user_id,
            duration=roulette_game.ban_duration
        )
