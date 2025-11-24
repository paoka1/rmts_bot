import json
from pathlib import Path

from openai.types.chat import ChatCompletionSystemMessageParam
from openai.types.chat import ChatCompletionUserMessageParam
from openai.types.chat import ChatCompletionAssistantMessageParam

def save_messages_to_file(messages, filename: str = "rosmontis_chat.json"):
    """保存消息历史到用户目录下的隐藏文件夹"""
    try:
        # 创建用户目录下的隐藏文件夹
        user_home = Path.home()
        hidden_dir = user_home / ".rmts_chat"
        hidden_dir.mkdir(exist_ok=True)
        
        # 完整文件路径
        filepath = hidden_dir / filename
        
        # 将消息转换为可序列化的格式
        serializable_messages = []
        for msg in messages:
            serializable_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_messages, f, ensure_ascii=False, indent=2)
        
        print(f"消息已保存到: {filepath}")
        return True
    except Exception as e:
        print(f"保存消息失败: {e}")
        return False

def load_messages_from_file(filename: str = "rosmontis_chat.json"):
    """从用户目录下的隐藏文件夹加载消息历史"""
    try:
        # 获取隐藏文件夹路径
        user_home = Path.home()
        hidden_dir = user_home / ".rmts_chat"
        filepath = hidden_dir / filename
        
        if not filepath.exists():
            print(f"文件 {filepath} 不存在")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 重新构建消息列表
        messages = []
        for msg_data in data:
            role = msg_data["role"]
            content = msg_data["content"]
            
            if role == "system":
                messages.append(ChatCompletionSystemMessageParam(content=content, role="system"))
            elif role == "user":
                messages.append(ChatCompletionUserMessageParam(content=content, role="user"))
            elif role == "assistant":
                messages.append(ChatCompletionAssistantMessageParam(content=content, role="assistant"))
        
        print(f"消息已从 {filepath} 加载")
        return messages
    except Exception as e:
        print(f"加载消息失败: {e}")
        return []
