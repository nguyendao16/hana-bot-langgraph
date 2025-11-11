from langchain_ollama import ChatOllama
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from hana.modules.abilities import Abilities
import os
from dotenv import load_dotenv
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

class Brain:
    def __init__(self, powerby: str, 
                       persona: ChatPromptTemplate,
                       abilities: list,
                       ): 
        llm = ChatOllama(model=powerby, base_url=OLLAMA_HOST)
        if abilities:
            llm = llm.bind_tools(abilities)
        self.brain = persona | llm
        self.abilities_name = {ability.name: ability for ability in abilities}
    
    def filter_non_text(self, text: str) -> str:
        text = text.replace('\\n', ' ').replace('\\t', ' ').replace('\\r', '')
        text = text.replace('\\', '')
        
        filtered_chars = []
        for char in text:
            if char.isalnum() or char.isspace() or char in '.,!?;:\'"()-':
                filtered_chars.append(char)
        return ''.join(filtered_chars).strip()
    
    def __call__(self, state: dict):
        messages = state.get("messages")
        response = self.thinking(messages)

        if hasattr(response, 'content') and response.content:
            filtered_content = self.filter_non_text(response.content)
            response = AIMessage(
                content=filtered_content,
                additional_kwargs=getattr(response, 'additional_kwargs', {}),
                response_metadata=getattr(response, 'response_metadata', {})
            )
        
        state["hana_response"] = response
        return state
    
    def thinking(self, messages: list):
        while True:
            response = self.brain.invoke({"messages": messages})
            if hasattr(response, "tool_calls") and len(response.tool_calls) > 0:
                result = self.perform_ability(response.tool_calls)
                messages.append(result)
            else:
                return response

    def perform_ability(self, calling_ability):
        for ability in calling_ability:
            result = self.abilities_name[ability["name"]].invoke(ability["args"])
        
        ability_result = ToolMessage(content=result, 
                                     name=ability["name"], 
                                     tool_call_id=ability["id"],)
        return ability_result
    
    async def shortTerm_memory(self):
        pass

    async def longTerm_memory(self):
        pass