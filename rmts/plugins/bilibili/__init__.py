import asyncio

from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot import require, get_bot, get_driver

from .live_api import bli_live_status
from .config import Config
from .status import Status

global_config = get_driver().config
plugin_config = Config(**global_config.model_dump())
status_info = Status()

scheduler = require('nonebot_plugin_apscheduler').scheduler

@scheduler.scheduled_job('interval', seconds=plugin_config.live_request_interval)
async def bili_live_push():
    for uid in plugin_config.get_live_uid_list():
        live_status = await bli_live_status(int(uid))

        if live_status is None: # 请求或解析出错
            continue

        pre = status_info.get_live_status(uid)
        now = live_status.is_live()
        status_info.set_live_status(uid, now)

        if not pre and now:  # 由未开播变为开播
            message = MessageSegment.text(f"{live_status.name}开播了！{live_status.room.title}")\
                                    +MessageSegment.image(live_status.room.cover)\
                                    +MessageSegment.text(live_status.room.url)
            for gid in plugin_config.get_live_group_list(uid):
                await get_bot().send_group_msg(group_id=int(gid), message=message)
                await asyncio.sleep(1)
        await asyncio.sleep(1)
