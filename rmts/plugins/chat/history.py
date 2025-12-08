import json
import aiofiles

from typing import Optional
from pathlib import Path
from nonebot.log import logger

from openai.types.chat import ChatCompletionSystemMessageParam
from openai.types.chat import ChatCompletionUserMessageParam
from openai.types.chat import ChatCompletionAssistantMessageParam
from openai.types.chat import ChatCompletionToolMessageParam

async def save_messages_to_file(messages, group_id: Optional[int] = None, filename: str = "rosmontis_chat.json"):
    """保存消息历史到用户目录下的隐藏文件夹
    
    Args:
        messages: 要保存的消息列表
        group_id: 群号,用于区分不同群组的聊天记录
        filename: 基础文件名,如果提供了群号会自动加上群号后缀
    """
    try:
        # 创建用户目录下的隐藏文件夹
        user_home = Path.home()
        hidden_dir = user_home / ".rmts_chat"
        hidden_dir.mkdir(exist_ok=True)
        
        # 根据群号生成文件名
        if group_id:
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'json'
            filename = f"{base_name}_group_{group_id}.{extension}"
        
        # 完整文件路径
        filepath = hidden_dir / filename
        
        # 将消息转换为可序列化的格式
        serializable_messages = []
        for msg in messages:
            msg_dict = {
                "role": msg["role"],
                "content": msg.get("content")
            }
            
            # 处理 assistant 消息的 tool_calls
            if msg["role"] == "assistant" and "tool_calls" in msg:
                msg_dict["tool_calls"] = msg["tool_calls"]
            
            # 处理 tool 消息的 tool_call_id
            if msg["role"] == "tool" and "tool_call_id" in msg:
                msg_dict["tool_call_id"] = msg["tool_call_id"]
            
            serializable_messages.append(msg_dict)
        
        # 使用异步文件写入
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(serializable_messages, ensure_ascii=False, indent=2))
        
        logger.success(f"消息已保存到: {filepath}")
        return True
    except Exception as e:
        logger.error(f"保存消息失败: {e}")
        return False

async def load_messages_from_file(group_id: Optional[int] = None, filename: str = "rosmontis_chat.json"):
    """从用户目录下的隐藏文件夹加载消息历史"""
    try:
        user_home = Path.home()
        hidden_dir = user_home / ".rmts_chat"
        
        if group_id:
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'json'
            filename = f"{base_name}_group_{group_id}.{extension}"
        
        filepath = hidden_dir / filename
        
        if not filepath.exists():
            logger.warning(f"文件 {filepath} 不存在")
            return []
        
        # 使用异步文件读取
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = json.loads(content)
        
        # 重新构建消息列表
        messages = []
        for msg_data in data:
            role = msg_data["role"]
            content = msg_data.get("content")
            
            if role == "system":
                messages.append(ChatCompletionSystemMessageParam(content=content, role="system"))
            elif role == "user":
                messages.append(ChatCompletionUserMessageParam(content=content, role="user"))
            elif role == "assistant":
                msg_param = ChatCompletionAssistantMessageParam(content=content, role="assistant")
                if "tool_calls" in msg_data:
                    msg_param["tool_calls"] = msg_data["tool_calls"]
                messages.append(msg_param)
            elif role == "tool":
                messages.append(ChatCompletionToolMessageParam(
                    role="tool",
                    tool_call_id=msg_data["tool_call_id"],
                    content=content
                ))
        
        logger.success(f"消息已从 {filepath} 加载")
        return messages
    except Exception as e:
        logger.error(f"加载消息失败: {e}")
        return []

def delete_messages_file(group_id: Optional[int] = None, filename: str = "rosmontis_chat.json"):
    """删除指定群组的消息历史文件
    
    Args:
        group_id: 群号,用于区分不同群组的聊天记录
        filename: 基础文件名,如果提供了群号会自动加上群号后缀
    
    Returns:
        bool: 删除成功返回 True,文件不存在或删除失败返回 False
    """
    try:
        # 获取隐藏文件夹路径
        user_home = Path.home()
        hidden_dir = user_home / ".rmts_chat"
        
        # 根据群号生成文件名
        if group_id:
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'json'
            filename = f"{base_name}_group_{group_id}.{extension}"
        
        filepath = hidden_dir / filename
        
        if not filepath.exists():
            logger.warning(f"文件 {filepath} 不存在,无需删除")
            return False
        
        filepath.unlink()
        logger.success(f"消息历史已删除: {filepath}")
        return True
    except Exception as e:
        logger.error(f"删除消息历史失败: {e}")
        return False
