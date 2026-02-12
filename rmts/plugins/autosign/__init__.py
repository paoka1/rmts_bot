from nonebot import require
from nonebot import get_driver, get_bot
from nonebot import logger

from rmts.utils.config import split_groups_int

scheduler = require('nonebot_plugin_apscheduler').scheduler

# 读取配置信息
config = get_driver().config
available_groups = split_groups_int(config.autosign_available_groups)
sign_time = config.autosign_time.split(':')
# 支持 HH:MM 或 HH:MM:SS 格式
if len(sign_time) == 2:
    sign_time = (int(sign_time[0]), int(sign_time[1]), 0)
else:
    sign_time = (int(sign_time[0]), int(sign_time[1]), int(sign_time[2]))

@scheduler.scheduled_job('cron', hour=sign_time[0], minute=sign_time[1], second=sign_time[2])
async def scheduled_autosign():
    bot = get_bot()
    for group_id in available_groups:
        try:
            await bot.call_api("send_group_sign", group_id=group_id)
        except Exception as e:
            logger.warning(f"自动群内打卡失败，群号: {group_id}, 错误: {e}")
