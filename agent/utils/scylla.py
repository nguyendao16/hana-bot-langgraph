import asyncio
import uuid
from datetime import datetime
from scyllapy import Scylla as ScyllaClient

class ScyllaManager:
    _session = None

    @classmethod
    async def initialize_session(cls, hosts: list, keyspace: str):
        if cls._session is None:
            print(f"Initializing ScyllaDB session for keyspace '{keyspace}'...")
            cls._session = ScyllaClient(hosts, keyspace=keyspace)
            await cls._session.startup()

    @classmethod
    async def close_session(cls):
        if cls._session:
            print("Closing ScyllaDB session pool...")
            await cls._session.shutdown()
            cls._session = None

    def __init__(self):
        if ScyllaManager._session is None:
            raise RuntimeError("Session has not been initialized. Call initialize_session() first.")
        self.session = ScyllaManager._session

    async def ScyllaDB(self, channel_name: str, users_id: str, user_mess: str, bot_mess: str):
        time_stamp = datetime.now()
        clean_users_id = users_id.replace("-", "")
        table_name = f"{channel_name}{clean_users_id}"

        create_table_cql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            channel_name text, act_id uuid, users_id text, 
            user_mess text, bot_mess text, time_stamp text, 
            PRIMARY KEY (users_id, act_id)
        ) WITH CLUSTERING ORDER BY (act_id DESC)
        """
        insert_data_cql = f"""
        INSERT INTO {table_name} (channel_name, act_id, users_id, user_mess, bot_mess, time_stamp) 
        VALUES (:channel, :act_id, :users_id, :user_mess, :bot_mess, :ts)
        """

        try:
            await self.session.execute(create_table_cql)
            await self.session.execute(
                insert_data_cql, 
                params={
                    "channel": channel_name, "act_id": uuid.uuid4(),
                    "users_id": clean_users_id, "user_mess": user_mess,
                    "bot_mess": bot_mess, "ts": str(time_stamp)
                }
            )
            print(f"Successfully saved message to table '{table_name}'.")
        except Exception as e:
            print(f"Error saving message to ScyllaDB: {e}")

    async def get_Scylla(self, channel_name: str, users_id: str, redis_client=None, limit: int = 5):
        thread_id = users_id
        try:
            clean_users_id = users_id.replace("-", "")
        except:
            clean_users_id = users_id
        
        table_name = f"{channel_name}{clean_users_id}"
        
        select_cql = f"SELECT user_mess, bot_mess FROM {table_name} WHERE users_id = :users_id LIMIT {limit}"
        
        try:
            rows = await self.session.execute(select_cql, params={"users_id": clean_users_id})
            if rows:
                all_rows = rows.all()
                chat_history = []

                for row in all_rows:
                    if redis_client:
                        try:
                            await redis_client.list_history_scylla(thread_id, row["user_mess"])
                            await redis_client.list_history_scylla(thread_id, row["bot_mess"])
                        except Exception as redis_error:
                            print(f"Redis sync error: {redis_error}")
                    
                    chat_history.append(f"User: {row["user_mess"]}, Bot: {row["bot_mess"]}.")
                
                return " ".join(reversed(chat_history))
            else:
                return None
        except Exception as e:
            print(f"Could not fetch history from table '{table_name}': {e}")
            return None
async def main():
    SCYLLA_HOSTS = ["100.73.237.108:9042", "100.73.237.108:9043"]
    KEYSPACE = "chat_mess"
    
    pool = ScyllaManager(SCYLLA_HOSTS, KEYSPACE)
    
    try:
        await pool.connect()
        session = pool.session
        print("\n--- Testing INSERT ---")
        await ScyllaDB(session, "none", "test1759506reerre422190", "Hello from user!", "Hello from bot!")
        print("\n--- Testing SELECT ---")
        chat_history = await get_Scylla(session, "none", "test1759506reerre422190", limit=10)
        if chat_history:
            print("Retrieved chat history:")
            print(chat_history)
        else:
            print("No chat history found or an error occurred.")
    except Exception as e:
        print(f"An application-level error occurred: {e}")
    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(main())