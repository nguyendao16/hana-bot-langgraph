import uvicorn
from os import getenv
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
import json
import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pathlib import Path
from hana.modules.abilities import rag_search
from hana.modules.brain import Brain
from hana.modules.ears import Ears
from hana.modules.mouth import Mouth
from hana.hana import Hana

load_dotenv()
OLLAMA_MODEL = getenv("OLLAMA_MODEL")
KITTENML_MODEL = getenv("KITTENML_MODEL")
KITTENML_VOICE = getenv("KITTENML_VOICE")
REALTIMETTS_MODEL = getenv("REALTIMETTS_MODEL")

if __name__ == '__main__':
    current_dir = Path(__file__).parent
    prompt_path = current_dir / 'hana/persona.txt'
    with open(prompt_path, 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read()

    persona = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), 
                                                MessagesPlaceholder(variable_name="messages")])
    abilities = [rag_search]
    HanaBrain = Brain(powerby=OLLAMA_MODEL, 
                  persona=persona, 
                  abilities=abilities,)
    HanaMouth = Mouth(powerby=KITTENML_MODEL, 
                    voice=KITTENML_VOICE)
    HanaEars = Ears(powerby=REALTIMETTS_MODEL)

    Hana = Hana(brain=HanaBrain, 
                ears=HanaEars, 
                mouth=HanaMouth,)
    Hana.CraftingHana()
    Hana.AskHana()
