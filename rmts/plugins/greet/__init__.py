from nonebot import get_driver
from nonebot import get_bot

from datetime import datetime

from rmts.utils.action import send_group_msg
from rmts.utils.config import split_groups

config = get_driver().config
available_groups = split_groups(config.greet_available_groups)
napcat_url = config.napcat_url
napcat_port = config.napcat_port
napcat_token = config.napcat_token

def get_greeting():
    """根据当前时间返回合适的问候语"""
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        return "大家早上好~"
    elif 12 <= current_hour < 14:
        return "大家中午好~"
    elif 14 <= current_hour < 18:
        return "大家下午好~"
    elif 18 <= current_hour < 22:
        return "大家晚上好~"
    else:
        return "大家好~"

driver = get_driver()

@driver.on_bot_connect
async def say_hello():
    if available_groups == []:
        return
    greeting = get_greeting()
    bot = get_bot()
    for group_id in available_groups:
        await bot.send_group_msg(group_id=group_id, message=greeting)

# @driver.on_shutdown
# async def say_goodbye():
#     if available_groups == ['']:
#         return
#     for group_id in available_groups:
#         await send_group_msg(
#             group_id=group_id,
#             message="香香想休息一会，等下再来和大家聊天~",
#             api_url=napcat_url,
#             api_port=napcat_port,
#             access_token=napcat_token
#             )
