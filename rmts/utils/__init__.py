from functools import wraps
from nonebot import logger
from nonebot.exception import FinishedException

from .rate_limiter import TokenBucket

# 全局限流器
global_rate_limiter = TokenBucket(capacity=10, rate=0.5)

async def acquire_global_token(tokens: float = 1) -> None:
    """
    尝试获取全局令牌，如果无法获取则抛出 FinishedException
    """

    if await global_rate_limiter.acquire_async(tokens):
        return
    
    logger.warning(f"Failed to acquire global tokens: {tokens}")
    raise FinishedException()

def acquire_global_token_decorator(tokens: float = 1):
    """
    获取全局令牌的装饰器，如果无法获取则抛出 FinishedException，结束当前事件处理
    
    Args:
        tokens: 需要获取的令牌数量，默认为 1
        
    Usage:
        @some_handler.handle()
        @acquire_global_token_decorator(tokens=2)
        async def handle_message(bot: Bot, event: MessageEvent):
            pass
    """
    def decorator(func):
        @wraps(func)  # 保留原函数的元数据，确保 NoneBot 依赖注入正常工作
        async def wrapper(*args, **kwargs):
            await acquire_global_token(tokens)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
