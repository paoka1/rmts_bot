from nonebot import get_driver
from nonebot.rule import is_type, to_me
from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from rmts.utils.config import split_groups

from .status import MinecraftServerStatus

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

fullmatch_words = ("查询服务器状态", "服务器状态", "查询状态")
query_status_handler = on_fullmatch(fullmatch_words, rule=to_me() & is_type(GroupMessageEvent), priority=2, block=True)

@query_status_handler.handle()
async def handle_query_status(event: GroupMessageEvent):
    if str(event.group_id) not in available_groups:
        await query_status_handler.finish("功能未启用")

    status = server.get_status()
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
            text += "在线玩家："
            for i, player in enumerate(sample, 1):
                player_name = player.get('name', '未知玩家')
                text += f"{i}. {player_name}，"
        elif online_count > 0:
            text += "玩家列表不可用"
        else:
            text += "当前无玩家在线"
    
    await query_status_handler.finish(MessageSegment.reply(event.message_id) + text)
