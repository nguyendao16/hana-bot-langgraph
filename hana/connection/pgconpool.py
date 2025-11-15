import asyncpg

class PostgresService:
    _pool = None 
    @classmethod
    async def initialize_pool(cls, host, database, user, password, port):
        if cls._pool is None:
            print("Initializing the shared connection pool for Postgres...")
            cls._pool = await asyncpg.create_pool(
                host=host,
                port=port,
                database=database, 
                user=user, 
                password=password
            )
    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            print("Closing Postgres connection pool...")
    def __inti__(self):
        if self._pool is None:
            raise RuntimeError("Pool has not been initialized. Call initialize_pool() first.")
    
    async def execute(self, query, *args):
        async with self._pool.acquire() as connection:
            return await connection.execute(query, *args)
    
    async def fetch(self, query, *args):
        async with self._pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    async def fetchrow(self, query, *args):
        async with self._pool.acquire() as connection:
            return await connection.fetchrow(query, *args)
