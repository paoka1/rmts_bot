"""
Minecraft服务器状态查询模块
使用mcstatus库查询Minecraft服务器的公开信息
"""

import asyncio
from typing import Dict, Any, Optional
from mcstatus import JavaServer


class MinecraftServerStatus:
    """
    Minecraft服务器状态查询类
    使用mcstatus库实现异步查询
    """
    
    def __init__(self, host: str, port: int = 25565, timeout: float = 5.0):
        """
        初始化服务器查询对象
        
        Args:
            host: 服务器地址
            port: 服务器端口，默认25565
            timeout: 连接超时时间，默认5秒
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._server = JavaServer(host, port)
    
    async def async_get_status(self, ignore_fake_players: bool = False) -> Optional[Dict[str, Any]]:
        """
        异步查询服务器状态
        
        Args:
            ignore_fake_players: 是否忽略fake_开头的玩家，默认False
        
        Returns:
            服务器状态信息字典，包含以下字段：
            - version: 版本信息 (name, protocol)
            - players: 玩家信息 (max, online, sample)
            - description: 服务器描述
            - favicon: 服务器图标（base64编码）
            如果查询失败则返回None
        """
        try:
            # 使用异步方法查询状态
            status = await asyncio.wait_for(
                self._server.async_status(),
                timeout=self.timeout
            )
            
            # 构建返回字典，保持与原实现一致的格式
            result = {
                'version': {
                    'name': status.version.name,
                    'protocol': status.version.protocol
                },
                'players': {
                    'max': status.players.max,
                    'online': status.players.online,
                    'sample': []
                },
                'description': status.description
            }
            
            # 添加在线玩家列表（如果有）
            if status.players.sample:
                players = [
                    {'name': player.name, 'id': player.id}
                    for player in status.players.sample
                ]
                
                # 如果启用了过滤fake_开头的玩家
                if ignore_fake_players:
                    players = [p for p in players if not p['name'].startswith('fake_')]
                    # 更新在线人数
                    result['players']['online'] = len(players)
                
                result['players']['sample'] = players
            
            # 添加favicon（如果有）
            if hasattr(status, 'icon') and status.icon:
                result['favicon'] = status.icon
            
            return result
            
        except asyncio.TimeoutError:
            print(f"连接超时: {self.host}:{self.port}")
            return None
        except Exception as e:
            print(f"查询失败: {e}")
            return None
    
    def __repr__(self) -> str:
        return f"MinecraftServerStatus(host='{self.host}', port={self.port})"


class MinecraftPlayerStatus:
    """
    Minecraft玩家状态类
    用于表示玩家的在线状态
    """

    def __init__(self) -> None:
        # 在线玩家列表
        self.online_players = set()
        # 首次检查标志，用于防止启动时推送消息
        self.is_first_check = True

    def update_status(self, server_status: bool, online_players: Optional[set]) -> Optional[Dict[str, Any]]:
        """
        更新玩家状态
        
        Args:
            server_status: 服务器当前在线状态
            online_players: 当前在线玩家列表
            
        Returns:
            如果有玩家状态变化，返回变化信息字典，否则返回None
            注意：首次调用时只会更新状态，不会返回变化信息
        """
        changes = {}
        
        if not server_status:
            # 服务器离线，清空在线玩家列表
            if self.online_players:
                changes['newly_offline'] = list(self.online_players)
                self.online_players.clear()
        else:
            # 服务器在线，检查玩家状态变化
            new_online_players = online_players if online_players is not None else set()
            
            # 检查新上线的玩家
            newly_online = new_online_players - self.online_players
            if newly_online:
                changes['newly_online'] = list(newly_online)
            
            # 检查下线的玩家
            newly_offline = self.online_players - new_online_players
            if newly_offline:
                changes['newly_offline'] = list(newly_offline)
            
            # 更新当前在线玩家列表
            self.online_players = new_online_players
        
        # 首次检查时，只更新状态不返回变化
        if self.is_first_check:
            self.is_first_check = False
            return None
        
        return changes if changes else None
