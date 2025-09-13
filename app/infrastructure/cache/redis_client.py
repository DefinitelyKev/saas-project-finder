from typing import Any, Optional, Dict, Union
import json
import redis.asyncio as redis
from redis.asyncio import Redis
import structlog

logger = structlog.get_logger(__name__)


class RedisClient:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[Redis] = None
    
    async def initialize(self) -> None:
        """Initialize Redis connection"""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            
            # Test connection
            await self.client.ping()
            logger.info("Redis client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Redis client", error=str(e))
            raise
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis client closed")
    
    async def set(
        self, 
        key: str, 
        value: Union[str, Dict[str, Any], Any], 
        expire: Optional[int] = None
    ) -> bool:
        """Set a key-value pair"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = await self.client.set(key, value, ex=expire)
            return result
        except Exception as e:
            logger.error("Redis SET error", key=key, error=str(e))
            raise
    
    async def get(self, key: str) -> Any:
        """Get value by key"""
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error("Redis GET error", key=key, error=str(e))
            raise
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error("Redis DELETE error", key=key, error=str(e))
            raise
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            logger.error("Redis EXISTS error", key=key, error=str(e))
            raise
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        try:
            result = await self.client.expire(key, seconds)
            return result
        except Exception as e:
            logger.error("Redis EXPIRE error", key=key, error=str(e))
            raise
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        try:
            result = await self.client.incr(key, amount)
            return result
        except Exception as e:
            logger.error("Redis INCR error", key=key, error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False