import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")
import discord
import asyncio
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pathlib import Path
from hana.modules.abilities import Abilities
from hana.modules.brain import Brain, Memory
from hana.modules.ears import Ears
from hana.modules.mouth import Mouth
from hana.hana import Hana
from hana.connection.google_service import GoogleService
from hana.connection.redisconpool import RedisService
from hana.connection.pgconpool import PostgresService
from hana.connection.discord_handler import Discord

load_dotenv()
OLLAMA_MODEL = getenv("OLLAMA_MODEL")
GEMINI_MODEL = getenv("GEMINI_MODEL")
OPENAI_MODEL = getenv("OPENAI_MODEL")

KITTENML_MODEL = getenv("KITTENML_MODEL")
KITTENML_VOICE = getenv("KITTENML_VOICE")
REALTIMETTS_MODEL = getenv("REALTIMETTS_MODEL")

GOOGLE_SERVICE_API = getenv("GOOGLE_SERVICE_API")
GOOGLE_CX = getenv("GOOGLE_CX")

REDIS_URL = getenv("REDIS_URL")
DISCORD_TOKEN = getenv("DISCORD_TOKEN")

PG_HOST = getenv("PG_HOST")
PG_DBNAME = getenv("PG_DBNAME")
PG_USER = getenv("PG_USER")
PG_PASSWORD = getenv("PG_PASSWORD")
PG_PORT = getenv("PG_PORT")

def cleanup_db():
    print("\n\nShutting down Hana...")
    try:
        RedisService.close_pool()
        PostgresService.close_pool()
        print("All connections closed successfully.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

def SetupHana():
    google_service = GoogleService(api_key=GOOGLE_SERVICE_API,
                                   cx=GOOGLE_CX,
                                   )
    google_service.build_google_service()
    
    RedisService.initialize_pool(url=REDIS_URL)
    redis_service = RedisService()

    PostgresService.initialize_pool(host=PG_HOST,
                                    database=PG_DBNAME,
                                    user=PG_USER,
                                    password=PG_PASSWORD,
                                    port=PG_PORT,
                                    )
    postgres_service = PostgresService()

    current_dir = Path(__file__).parent
    prompt_path = current_dir / 'hana/persona.txt'
    with open(prompt_path, 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read()

    persona = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), 
                                                MessagesPlaceholder(variable_name="messages")])
    HanaAbilities = Abilities(google_service=google_service,)
    abilities = HanaAbilities.get_abilities() 

    memory = Memory(redis_conn=redis_service, pg_con=postgres_service)
    
    HanaBrain = Brain(powerby=OPENAI_MODEL, 
                  persona=persona, 
                  abilities=abilities,
                  memory=memory,
                  )
    HanaMouth = Mouth(powerby=KITTENML_MODEL, 
                    voice=KITTENML_VOICE
                    )
    HanaEars = Ears(powerby=REALTIMETTS_MODEL)

    hana_instance = Hana(brain=HanaBrain, 
                         ears=HanaEars, 
                         mouth=HanaMouth,)
    hana_instance.CraftingHana()
    return hana_instance

if __name__ == '__main__':
    hana = SetupHana()
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = commands.Bot(command_prefix="*", intents=intents)
    executor = ThreadPoolExecutor(max_workers=1)
    
    hana_discord = Discord(
        bot=bot,
        hana=hana,
        executor=executor,
        token=DISCORD_TOKEN,
    )
    
    try:
        hana_discord.run()
    except KeyboardInterrupt:
        print("\n\n=== Hana Discord Bot is stopped ===")
    finally:
        print("Cleaning up all resources...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(hana_discord.cleanup_async())
            loop.close()
        except Exception as e:
            print(f"Error during Discord cleanup: {e}")
        
        cleanup_db()