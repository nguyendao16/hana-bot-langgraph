import redis.asyncio as redis

class RedisSaver:
    _pool = None 
    @classmethod
    def initialize_pool(cls, url, decode_responses=True):
        if cls._pool is None:
            print("Initializing the shared connection pool for RedisSaver...")
            cls._pool = redis.ConnectionPool.from_url(
                url=url,
                decode_responses=decode_responses
            )
    @classmethod
    async def get_client(cls):
        if cls._pool is None:
            raise RuntimeError("Pool has not been initialized. Call initialize_pool() first.")
        return await redis.Redis(connection_pool=cls._pool)
    
    @classmethod
    async def close_pool(cls):
        if cls._pool:
            print("Closing the shared async connection pool for RedisSaver...")
            await cls._pool.disconnect()
            cls._pool = None
    
    def __init__(self):
        if RedisSaver._pool is None:
            RedisSaver.initialize_pool()
        self.client = redis.Redis(connection_pool=RedisSaver._pool)

    async def get_message(self, key):
        return await self.client.get(key)

    async def isExist(self, key):
        return await self.client.exists(key)

    async def append_message(self, key, message):
        if await self.client.exists(key):
            await self.client.append(key, message)
        else:
            await self.client.set(key, message)
            await self.client.expire(key, 60)

    async def del_message(self, key):
        await self.client.delete(key)

    async def list_history(self, key, message, windows_length=10):
        llen = await self.client.llen(key)
        if await self.client.exists(key):
            await self.client.expire(key, 120)
            await self.client.rpush(key, message)
        elif llen < windows_length:
            await self.client.rpush(key, message)
        else:
            await self.client.ltrim(key, -windows_length, -1)
            await self.client.rpush(key, message)

    async def list_history_scylla(self, key, message, windows_length=10):
        llen = await self.client.llen(key)
        if await self.client.exists(key):
            await self.client.expire(key, 120)
            await self.client.lpush(key, message)
        elif llen < windows_length:
            await self.client.lpush(key, message)
        else:
            await self.client.ltrim(key, -windows_length, -1)
            await self.client.lpush(key, message)

    async def get_history(self, key):
        history_items = await self.client.lrange(key, 0, -1)
        return history_items

    async def is_member_in_set(self, set_name: str, member: str) -> bool:
        return await self.client.sismember(set_name, member) == 1

    async def add_to_set(self, set_name: str, member: str):
        await self.client.sadd(set_name, member)

    async def remove_from_set(self, set_name: str, member: str):
        await self.client.srem(set_name, member)

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    #RedisSaver.initialize_pool(host = os.getenv("REDIS_HOST"))
    #redis = RedisSaver()
    r = redis.Redis(host='20.2.9.81', port=6379, db=0, decode_responses=False)
    a = r.hgetall("llmcache:8aaecd06d85c7f743d3545e7b865f3053c647591f95919c1c0b003046d4757aa")

    print(a)