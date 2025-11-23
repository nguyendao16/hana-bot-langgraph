import redis

class RedisService:
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
    def get_client(cls):
        if cls._pool is None:
            raise RuntimeError("Pool has not been initialized. Call initialize_pool() first.")
        return redis.Redis(connection_pool=cls._pool)
    
    @classmethod
    def close_pool(cls):
        if cls._pool:
            print("Closing the shared connection pool for RedisSaver...")
            cls._pool.disconnect()
            cls._pool = None
    
    def __init__(self):
        if RedisService._pool is None:
            raise RuntimeError("Pool has not been initialized. Call initialize_pool() first.")
        self.client = redis.Redis(connection_pool=RedisService._pool)

    def get_message(self, key):
        return self.client.get(key)

    def isExist(self, key):
        return self.client.exists(key)

    def append_message(self, key, message):
        if self.client.exists(key):
            self.client.append(key, message)
        else:
            self.client.set(key, message)
            self.client.expire(key, 60)

    def del_message(self, key):
        self.client.delete(key)

    def list_history(self, key, message, windows_length=10):
        llen = self.client.llen(key)
        if self.client.exists(key):
            self.client.expire(key, 240)
            self.client.rpush(key, message)
        elif llen < windows_length:
            self.client.rpush(key, message)
        else:
            self.client.ltrim(key, -windows_length, -1)
            self.client.rpush(key, message)

    def list_history_scylla(self, key, message, windows_length=10):
        llen = self.client.llen(key)
        if self.client.exists(key):
            self.client.expire(key, 120)
            self.client.lpush(key, message)
        elif llen < windows_length:
            self.client.lpush(key, message)
        else:
            self.client.ltrim(key, -windows_length, -1)
            self.client.lpush(key, message)

    def get_history(self, key):
        history_items = self.client.lrange(key, 0, -1)
        return history_items

    def is_member_in_set(self, set_name: str, member: str) -> bool:
        return self.client.sismember(set_name, member) == 1

    def add_to_set(self, set_name: str, member: str):
        self.client.sadd(set_name, member)

    def remove_from_set(self, set_name: str, member: str):
        self.client.srem(set_name, member)

