"""令牌桶限流器

提供基于令牌桶算法的限流功能，支持同步和异步使用。
"""

import asyncio
import time
from threading import Lock
from typing import Optional


class TokenBucket:
    """令牌桶限流器
    
    使用令牌桶算法实现限流，支持同步和异步调用。
    
    Args:
        capacity: 桶的最大容量（最多存储的令牌数）
        rate: 令牌生成速率（每秒生成的令牌数）
    
    Example:
        >>> # 创建一个限流器，容量为10，每秒生成2个令牌
        >>> limiter = TokenBucket(capacity=10, rate=2)
        >>> 
        >>> # 同步使用
        >>> if limiter.acquire():
        >>>     print("请求通过")
        >>> else:
        >>>     print("请求被限流")
        >>> 
        >>> # 异步使用
        >>> if await limiter.acquire_async():
        >>>     print("请求通过")
    """
    
    def __init__(self, capacity: float, rate: float):
        """初始化令牌桶
        
        Args:
            capacity: 桶的最大容量
            rate: 令牌生成速率（每秒）
        """
        if capacity <= 0:
            raise ValueError("容量必须大于0")
        if rate <= 0:
            raise ValueError("生成速率必须大于0")
        
        self._capacity = float(capacity)
        self._rate = float(rate)
        self._tokens = float(capacity)  # 初始化时桶是满的
        self._last_update = time.time()
        self._lock = Lock()
    
    def _refill(self) -> None:
        """根据时间流逝补充令牌（内部方法，需要持有锁）"""
        now = time.time()
        elapsed = now - self._last_update
        
        # 计算应该添加的令牌数
        new_tokens = elapsed * self._rate
        self._tokens = min(self._capacity, self._tokens + new_tokens)
        self._last_update = now
    
    def acquire(self, tokens: float = 1.0) -> bool:
        """尝试获取指定数量的令牌（同步版本）
        
        Args:
            tokens: 需要获取的令牌数量，默认为1
        
        Returns:
            bool: 如果成功获取令牌返回True，否则返回False
        """
        if tokens <= 0:
            raise ValueError("令牌数量必须大于0")
        
        with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
    
    async def acquire_async(self, tokens: float = 1.0) -> bool:
        """尝试获取指定数量的令牌（异步版本）
        
        Args:
            tokens: 需要获取的令牌数量，默认为1
        
        Returns:
            bool: 如果成功获取令牌返回True，否则返回False
        """
        # 在异步环境中调用同步方法
        return await asyncio.to_thread(self.acquire, tokens)
    
    def wait_acquire(self, tokens: float = 1.0, timeout: Optional[float] = None) -> bool:
        """等待获取令牌（同步版本，会阻塞）
        
        Args:
            tokens: 需要获取的令牌数量，默认为1
            timeout: 超时时间（秒），None表示无限等待
        
        Returns:
            bool: 如果成功获取令牌返回True，超时返回False
        """
        if tokens <= 0:
            raise ValueError("令牌数量必须大于0")
        
        start_time = time.time()
        
        while True:
            if self.acquire(tokens):
                return True
            
            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            # 计算需要等待的时间
            with self._lock:
                self._refill()
                needed = tokens - self._tokens
                if needed > 0:
                    wait_time = needed / self._rate
                    # 如果有超时限制，等待时间不超过剩余时间
                    if timeout is not None:
                        remaining = timeout - (time.time() - start_time)
                        wait_time = min(wait_time, remaining)
                    if wait_time > 0:
                        time.sleep(min(wait_time, 0.1))  # 最多睡眠0.1秒，避免长时间阻塞
    
    async def wait_acquire_async(
        self, tokens: float = 1.0, timeout: Optional[float] = None
    ) -> bool:
        """等待获取令牌（异步版本，会阻塞）
        
        Args:
            tokens: 需要获取的令牌数量，默认为1
            timeout: 超时时间（秒），None表示无限等待
        
        Returns:
            bool: 如果成功获取令牌返回True，超时返回False
        """
        if tokens <= 0:
            raise ValueError("令牌数量必须大于0")
        
        start_time = time.time()
        
        while True:
            if await self.acquire_async(tokens):
                return True
            
            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            # 计算需要等待的时间
            with self._lock:
                self._refill()
                needed = tokens - self._tokens
                if needed > 0:
                    wait_time = needed / self._rate
                    # 如果有超时限制，等待时间不超过剩余时间
                    if timeout is not None:
                        remaining = timeout - (time.time() - start_time)
                        wait_time = min(wait_time, remaining)
                    if wait_time > 0:
                        await asyncio.sleep(min(wait_time, 0.1))
    
    @property
    def available_tokens(self) -> float:
        """获取当前可用的令牌数量"""
        with self._lock:
            self._refill()
            return self._tokens
    
    @property
    def capacity(self) -> float:
        """获取桶的容量"""
        return self._capacity
    
    @property
    def rate(self) -> float:
        """获取令牌生成速率"""
        return self._rate
    
    def reset(self) -> None:
        """重置令牌桶，将令牌数设置为满容量"""
        with self._lock:
            self._tokens = self._capacity
            self._last_update = time.time()
