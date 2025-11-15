import psycopg2
from psycopg2 import pool

class PostgresService:
    _pool = None 
    @classmethod
    def initialize_pool(cls, host, database, user, password, port, minconn=1, maxconn=10):
        if cls._pool is None:
            print("Initializing the shared connection pool for Postgres...")
            cls._pool = psycopg2.pool.SimpleConnectionPool(
                minconn,
                maxconn,
                host=host,
                port=port,
                database=database, 
                user=user, 
                password=password
            )
    @classmethod
    def close_pool(cls):
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
            print("Closing Postgres connection pool...")
    
    def __init__(self):
        if self._pool is None:
            raise RuntimeError("Pool has not been initialized. Call initialize_pool() first.")
    
    def execute(self, query, *args):
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                conn.commit()
                return cursor.rowcount
        finally:
            self._pool.putconn(conn)
    
    def fetch(self, query, *args):
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                return cursor.fetchall()
        finally:
            self._pool.putconn(conn)
    
    def fetchrow(self, query, *args):
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                return cursor.fetchone()
        finally:
            self._pool.putconn(conn)

