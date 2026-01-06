"""
Minecraft服务器状态查询模块
使用原生TCP协议查询Minecraft服务器的公开信息
"""

import socket
import struct
import json
from typing import Dict, Any, Optional, Tuple


class MinecraftServerStatus:
    """
    Minecraft服务器状态查询类
    使用Server List Ping (SLP)协议查询服务器状态信息
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
        
    def _pack_varint(self, value: int) -> bytes:
        """
        将整数打包为VarInt格式
        
        Args:
            value: 要打包的整数（必须是非负整数）
            
        Returns:
            VarInt格式的字节数据
        """
        if value < 0:
            raise ValueError(f"VarInt不支持负数: {value}")
            
        result = bytearray()
        while True:
            temp = value & 0x7F
            value >>= 7
            if value != 0:
                temp |= 0x80
            result.append(temp)
            if value == 0:
                break
        return bytes(result)
    
    def _unpack_varint(self, data: bytes, offset: int = 0) -> Tuple[int, int]:
        """
        从字节数据中解包VarInt
        
        Args:
            data: 字节数据
            offset: 起始偏移量
            
        Returns:
            (解包的整数值, 读取的字节数)
        """
        result = 0
        shift = 0
        bytes_read = 0
        
        while True:
            if offset + bytes_read >= len(data):
                raise ValueError("VarInt数据不完整")
                
            byte = data[offset + bytes_read]
            bytes_read += 1
            
            result |= (byte & 0x7F) << shift
            shift += 7
            
            if not (byte & 0x80):
                break
                
            if bytes_read > 5:
                raise ValueError("VarInt过长")
                
        return result, bytes_read
    
    def _create_handshake_packet(self) -> bytes:
        """
        创建握手数据包
        
        Returns:
            握手数据包字节数据
        """
        # 协议版本号 (使用-1需要特殊处理，这里使用47即1.8+的协议版本)
        # 对于状态查询，大多数服务器接受任何合理的协议版本号
        protocol_version = self._pack_varint(47)
        
        # 服务器地址
        server_address = self.host.encode('utf-8')
        server_address_length = self._pack_varint(len(server_address))
        
        # 服务器端口 (unsigned short)
        server_port = struct.pack('>H', self.port)
        
        # 下一个状态 (1表示status)
        next_state = self._pack_varint(1)
        
        # 组装数据
        data = protocol_version + server_address_length + server_address + server_port + next_state
        
        # 添加包ID (0x00 表示握手)
        packet_id = self._pack_varint(0x00)
        packet_data = packet_id + data
        
        # 添加包长度
        packet_length = self._pack_varint(len(packet_data))
        
        return packet_length + packet_data
    
    def _create_status_request_packet(self) -> bytes:
        """
        创建状态请求数据包
        
        Returns:
            状态请求数据包字节数据
        """
        # 包ID (0x00)
        packet_id = self._pack_varint(0x00)
        
        # 包长度
        packet_length = self._pack_varint(len(packet_id))
        
        return packet_length + packet_id
    
    def _read_packet(self, sock: socket.socket) -> bytes:
        """
        从socket读取一个完整的数据包
        
        Args:
            sock: socket对象
            
        Returns:
            数据包内容（不含长度字段）
        """
        # 读取包长度
        length_data = bytearray()
        while True:
            byte = sock.recv(1)
            if not byte:
                raise ConnectionError("连接已关闭")
            
            length_data.append(byte[0])
            
            # VarInt最后一个字节的最高位为0
            if not (byte[0] & 0x80):
                break
                
            if len(length_data) > 5:
                raise ValueError("包长度VarInt过长")
        
        packet_length, _ = self._unpack_varint(bytes(length_data))
        
        # 读取包内容
        packet_data = bytearray()
        remaining = packet_length
        
        while remaining > 0:
            chunk = sock.recv(remaining)
            if not chunk:
                raise ConnectionError("连接已关闭")
            packet_data.extend(chunk)
            remaining -= len(chunk)
        
        return bytes(packet_data)
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        查询服务器状态
        
        Returns:
            服务器状态信息字典，包含以下字段：
            - version: 版本信息 (name, protocol)
            - players: 玩家信息 (max, online, sample)
            - description: 服务器描述
            - favicon: 服务器图标（base64编码）
            如果查询失败则返回None
        """
        try:
            # 创建TCP连接
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
                
                # 发送握手包
                handshake_packet = self._create_handshake_packet()
                sock.sendall(handshake_packet)
                
                # 发送状态请求包
                status_request_packet = self._create_status_request_packet()
                sock.sendall(status_request_packet)
                
                # 读取响应
                response_data = self._read_packet(sock)
                
                # 解析响应
                packet_id, offset = self._unpack_varint(response_data)
                
                if packet_id != 0x00:
                    raise ValueError(f"意外的包ID: {packet_id}")
                
                # 读取JSON字符串长度
                json_length, bytes_read = self._unpack_varint(response_data, offset)
                offset += bytes_read
                
                # 读取JSON字符串
                json_data = response_data[offset:offset + json_length].decode('utf-8')
                
                # 解析JSON
                status = json.loads(json_data)
                
                return status
                
        except socket.timeout:
            print(f"连接超时: {self.host}:{self.port}")
            return None
        except socket.error as e:
            print(f"Socket错误: {e}")
            return None
        except Exception as e:
            print(f"查询失败: {e}")
            return None
    
    def get_simple_status(self) -> Optional[Dict[str, Any]]:
        """
        获取简化的服务器状态信息
        
        Returns:
            简化的状态信息字典，包含：
            - online: 是否在线
            - version: 服务器版本
            - players_online: 在线玩家数
            - players_max: 最大玩家数
            - description: 服务器描述
            如果查询失败则返回None
        """
        status = self.get_status()
        
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
    
    def __repr__(self) -> str:
        return f"MinecraftServerStatus(host='{self.host}', port={self.port})"


def query_server(host: str, port: int = 25565, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    """
    便捷函数：查询Minecraft服务器状态
    
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
