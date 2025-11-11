from os import getenv
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pathlib import Path
from hana.modules.abilities import Abilities
from hana.modules.brain import Brain
from hana.modules.ears import Ears
from hana.modules.mouth import Mouth
from hana.hana import Hana
from hana.connection.google_service import GoogleService

load_dotenv()
OLLAMA_MODEL = getenv("OLLAMA_MODEL")
KITTENML_MODEL = getenv("KITTENML_MODEL")
KITTENML_VOICE = getenv("KITTENML_VOICE")
REALTIMETTS_MODEL = getenv("REALTIMETTS_MODEL")
GOOGLE_SERVICE_API = getenv("GOOGLE_SERVICE_API")
GOOGLE_CX = getenv("GOOGLE_CX")

def CallHana():
    google_service = GoogleService(api_key=GOOGLE_SERVICE_API,
                                   cx=GOOGLE_CX
                                   )
    google_service.build_google_service()

    current_dir = Path(__file__).parent
    prompt_path = current_dir / 'hana/persona.txt'
    with open(prompt_path, 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read()

    persona = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), 
                                                MessagesPlaceholder(variable_name="messages")])
    HanaAbilities = Abilities(google_service=google_service,)
    abilities = HanaAbilities.get_abilities() 

    HanaBrain = Brain(powerby=OLLAMA_MODEL, 
                  persona=persona, 
                  abilities=abilities,
                  )
    HanaMouth = Mouth(powerby=KITTENML_MODEL, 
                    voice=KITTENML_VOICE
                    )
    HanaEars = Ears(powerby=REALTIMETTS_MODEL)

    hana_instance = Hana(brain=HanaBrain, 
                         ears=HanaEars, 
                         mouth=HanaMouth,)
    hana_instance.CraftingHana()
    hana_instance.AskHana()

if __name__ == '__main__':
    CallHana()
