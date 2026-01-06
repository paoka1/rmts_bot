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
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        同步查询服务器状态（内部使用asyncio）
        
        Returns:
            服务器状态信息字典，包含以下字段：
            - version: 版本信息 (name, protocol)
            - players: 玩家信息 (max, online, sample)
            - description: 服务器描述
            - favicon: 服务器图标（base64编码）
            如果查询失败则返回None
        """
        try:
            # 获取或创建事件循环
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # 没有运行中的循环，创建新的
                return asyncio.run(self.async_get_status())
            else:
                # 已经在事件循环中，创建任务
                return loop.run_until_complete(self.async_get_status())
        except Exception as e:
            print(f"查询失败: {e}")
            return None
    
    async def async_get_simple_status(self) -> Optional[Dict[str, Any]]:
        """
        异步获取简化的服务器状态信息
        
        Returns:
            简化的状态信息字典，包含：
            - online: 是否在线
            - version: 服务器版本
            - players_online: 在线玩家数
            - players_max: 最大玩家数
            - description: 服务器描述
            如果查询失败则返回None
        """
        status = await self.async_get_status()
        
        if not status:
            return {
                'online': False,
                'version': None,
                'players_online': 0,
                'players_max': 0,
                'description': None
            }
        
        # 提取描述文本
        description = status.get('description', {})
        if isinstance(description, dict):
            desc_text = description.get('text', '')
        else:
            desc_text = str(description)
        
        return {
            'online': True,
            'version': status.get('version', {}).get('name', 'Unknown'),
            'players_online': status.get('players', {}).get('online', 0),
            'players_max': status.get('players', {}).get('max', 0),
            'description': desc_text
        }
    
    def get_simple_status(self) -> Optional[Dict[str, Any]]:
        """
        同步获取简化的服务器状态信息
        
        Returns:
            简化的状态信息字典，包含：
            - online: 是否在线
            - version: 服务器版本
            - players_online: 在线玩家数
            - players_max: 最大玩家数
            - description: 服务器描述
            如果查询失败则返回None
        """
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(self.async_get_simple_status())
            else:
                return loop.run_until_complete(self.async_get_simple_status())
        except Exception as e:
            print(f"查询失败: {e}")
            return None
    
    def __repr__(self) -> str:
        return f"MinecraftServerStatus(host='{self.host}', port={self.port})"


async def async_query_server(host: str, port: int = 25565, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    """
    便捷函数：异步查询Minecraft服务器状态
    
    Args:
        host: 服务器地址
        port: 服务器端口，默认25565
        timeout: 超时时间，默认5秒
        
    Returns:
        服务器状态信息字典，失败返回None
    """
    server = MinecraftServerStatus(host, port, timeout)
    return await server.async_get_status()


def query_server(host: str, port: int = 25565, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    """
    便捷函数：同步查询Minecraft服务器状态
    
    Args:
        host: 服务器地址
        port: 服务器端口，默认25565
        timeout: 超时时间，默认5秒
        
    Returns:
        服务器状态信息字典，失败返回None
    """
    server = MinecraftServerStatus(host, port, timeout)
    return server.get_status()


if __name__ == '__main__':
    import json
    
    # 示例用法
    address = input("请输入Minecraft服务器地址 (格式: host:port): ")
    if ':' in address:
        host, port_str = address.split(':', 1)
        port = int(port_str)
    else:
        host = address
        port = 25565
    server = MinecraftServerStatus(host, port, timeout=5.0)
    
    # 获取完整状态
    status = server.get_status()
    if status:
        print("服务器状态:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    # 获取简化状态
    simple_status = server.get_simple_status()
    if simple_status:
        print("\n简化状态:")
        print(f"在线: {simple_status['online']}")
        print(f"版本: {simple_status['version']}")
        print(f"玩家: {simple_status['players_online']}/{simple_status['players_max']}")
        print(f"描述: {simple_status['description']}")
