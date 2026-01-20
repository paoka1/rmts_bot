from nonebot import require
from nonebot import get_driver, get_bot
from nonebot.rule import is_type, to_me
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import MessageSegment, Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from rmts.utils.config import split_groups

from .status import MinecraftServerStatus
from .status import MinecraftPlayerStatus

scheduler = require('nonebot_plugin_apscheduler').scheduler

# 读取配置信息
config = get_driver().config
# mc 服务器地址信息，形如：xxx.xxx.xxx:xxxx
server_addr = config.minecraft_server_address
# 可用的群组列表
available_groups = config.minecraft_status_available_groups
available_groups = split_groups(available_groups)

# 解析服务器地址和端口
if ':' in server_addr:
    host, port_str = server_addr.split(':', 1)
    port = int(port_str)
else:
    host = server_addr
    port = 25565

# 创建Minecraft服务器状态查询对象
server = MinecraftServerStatus(host, port, timeout=5.0)
player_status = MinecraftPlayerStatus()

fullmatch_words = ("查询服务器状态", "服务器状态", "查询状态", "状态查询")
query_status_handler = on_fullmatch(fullmatch_words, rule=to_me() & is_type(GroupMessageEvent), priority=2, block=True)

@query_status_handler.handle()
async def handle_query_status(event: GroupMessageEvent):
    if str(event.group_id) not in available_groups:
        await query_status_handler.finish("功能未启用")

    status = await server.async_get_status(ignore_fake_players=True)
    if not status:
        # 服务器离线
        text = f"服务器离线:("
    else:
        # 服务器在线
        players_info = status.get('players', {})
        online_count = players_info.get('online', 0)
        max_count = players_info.get('max', 0)
        
        # 构建基本信息
        text = f"服务器在线:)\n"
        text += f"在线人数: {online_count}/{max_count}\n"
        
        # 获取在线玩家列表
        sample = players_info.get('sample', [])
        if sample and online_count > 0:
            player_names = [player.get('name', '未知玩家') for player in sample]
            text += "在线玩家：" + "，".join(player_names)
        elif online_count > 0:
            text += "玩家列表不可用"
        else:
            text += "当前无玩家在线"
    
    await query_status_handler.finish(MessageSegment.reply(event.message_id) + text)


# 定时任务，定期查询服务器状态，并推送玩家状态变化
@scheduler.scheduled_job('interval', seconds=60)  # 每一分钟执行一次
async def scheduled_minecraft_status_check():
    """定时检查服务器状态并推送玩家变化信息"""
    # 查询服务器状态
    status = await server.async_get_status(ignore_fake_players=True)
    
    # 解析在线玩家
    if status:
        players_info = status.get('players', {})
        sample = players_info.get('sample', [])
        online_players = set(player.get('name') for player in sample if player.get('name'))
        changes = player_status.update_status(server_status=True, online_players=online_players)
    else:
        # 服务器离线
        changes = player_status.update_status(server_status=False, online_players=None)
    
    # 如果有变化，构建消息并推送
    if changes:
        message_parts = []
        
        # 处理上线玩家
        if 'newly_online' in changes:
            online_players = changes['newly_online']
            message_parts.append(f"{'、'.join(online_players)}上线了")
        
        # 处理下线玩家
        if 'newly_offline' in changes:
            offline_players = changes['newly_offline']
            message_parts.append(f"{'、'.join(offline_players)}下线了")
        
        # 合并消息
        if message_parts:
            message_text = "玩家：" + "，".join(message_parts)
            
            # 向所有可用群组推送消息
            bot = get_bot()
            for group_id in available_groups:
                try:
                    await bot.send_group_msg(group_id=int(group_id), message=message_text)
                except Exception as e:
                    print(f"向群 {group_id} 发送消息失败: {e}")

