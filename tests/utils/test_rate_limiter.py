"""令牌桶限流器测试"""

import pytest

from rmts.utils.rate_limiter import TokenBucket


class TestTokenBucketBasic:
    """基本功能测试"""
    
    def test_init_valid_params(self):
        """测试正常初始化"""
        limiter = TokenBucket(capacity=10, rate=2)
        assert limiter.capacity == 10
        assert limiter.rate == 2
        assert limiter.available_tokens == 10  # 初始化时桶是满的
    
    def test_init_invalid_capacity(self):
        """测试无效容量"""
        with pytest.raises(ValueError, match="容量必须大于0"):
            TokenBucket(capacity=0, rate=2)
        
        with pytest.raises(ValueError, match="容量必须大于0"):
            TokenBucket(capacity=-1, rate=2)
    
    def test_init_invalid_rate(self):
        """测试无效速率"""
        with pytest.raises(ValueError, match="生成速率必须大于0"):
            TokenBucket(capacity=10, rate=0)
        
        with pytest.raises(ValueError, match="生成速率必须大于0"):
            TokenBucket(capacity=10, rate=-1)


class TestTokenBucketAcquire:
    """令牌获取测试"""
    
    def test_acquire_single_token(self):
        """测试获取单个令牌"""
        limiter = TokenBucket(capacity=5, rate=1)
        assert limiter.acquire() is True
        assert limiter.available_tokens == 4
    
    def test_acquire_multiple_tokens(self):
        """测试获取多个令牌"""
        limiter = TokenBucket(capacity=10, rate=1)
        assert limiter.acquire(3) is True
        assert limiter.available_tokens == 7
    
    def test_acquire_insufficient_tokens(self):
        """测试令牌不足"""
        limiter = TokenBucket(capacity=5, rate=1)
        assert limiter.acquire(3) is True
        assert limiter.acquire(3) is False  # 只剩2个，获取失败
        assert limiter.available_tokens == 2
    
    def test_acquire_exact_tokens(self):
        """测试精确获取所有令牌"""
        limiter = TokenBucket(capacity=5, rate=1)
        assert limiter.acquire(5) is True
        assert limiter.available_tokens == 0
        assert limiter.acquire(1) is False
    
    def test_acquire_invalid_tokens(self):
        """测试无效的令牌数量"""
        limiter = TokenBucket(capacity=5, rate=1)
        
        with pytest.raises(ValueError, match="令牌数量必须大于0"):
            limiter.acquire(0)
        
        with pytest.raises(ValueError, match="令牌数量必须大于0"):
            limiter.acquire(-1)


class TestTokenBucketProperties:
    """属性测试"""
    
    def test_available_tokens(self):
        """测试可用令牌属性"""
        limiter = TokenBucket(capacity=10, rate=2)
        assert limiter.available_tokens == 10
        
        limiter.acquire(3)
        assert limiter.available_tokens == 7
    
    def test_capacity_property(self):
        """测试容量属性"""
        limiter = TokenBucket(capacity=15, rate=3)
        assert limiter.capacity == 15
    
    def test_rate_property(self):
        """测试速率属性"""
        limiter = TokenBucket(capacity=10, rate=5)
        assert limiter.rate == 5
    
    def test_reset(self):
        """测试重置功能"""
        limiter = TokenBucket(capacity=10, rate=1)
        
        # 消耗一些令牌
        limiter.acquire(7)
        assert limiter.available_tokens == 3
        
        # 重置
        limiter.reset()
        assert limiter.available_tokens == 10
