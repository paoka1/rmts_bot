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
    
    async def async_get_status(self) -> Optional[Dict[str, Any]]:
        """
        异步查询服务器状态
        
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
                result['players']['sample'] = [
                    {'name': player.name, 'id': player.id}
                    for player in status.players.sample
                ]
            
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
