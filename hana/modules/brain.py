from langchain_ollama import ChatOllama
from langchain_core.messages import ToolMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from hana.modules.state import State
from hana.modules.abilities import Abilities
from hana.connection.redisconpool import RedisService
import os
from dotenv import load_dotenv
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

class Brain:
    def __init__(self, powerby: str, 
                       persona: ChatPromptTemplate,
                       abilities: list,
                       memory = None,
                       ): 
        llm = ChatOllama(model=powerby, base_url=OLLAMA_HOST)
        if abilities:
            llm = llm.bind_tools(abilities)
        self.brain = persona | llm
        self.abilities_name = {ability.name: ability for ability in abilities}
        self.memory = memory
    
    def filter_non_text(self, text: str) -> str:
        text = text.replace('\\n', ' ').replace('\\t', ' ').replace('\\r', '')
        text = text.replace('\\', '')
        
        filtered_chars = []
        for char in text:
            if char.isalnum() or char.isspace() or char in '.,!?;:\'"()-':
                filtered_chars.append(char)
        return ''.join(filtered_chars).strip()
    
    def __call__(self, state: State):
        messages = state.get("messages")
        conversant = state.get("conversant")

        if messages and len(messages) > 0:
            original_content = messages[0].content
            messages[0].content = f"{conversant} is takling to you: {original_content}"
        
        history = self.recall_memory(type="shortTerm_memory", state=state)
        messages = [(SystemMessage(content=f"Conversation history: {history}"))] + messages
        
        response = self.thinking(messages)
        
        if hasattr(response, 'content') and response.content:
            filtered_content = self.filter_non_text(response.content)
            response = AIMessage(
                content=filtered_content,
                additional_kwargs=getattr(response, 'additional_kwargs', {}),
                response_metadata=getattr(response, 'response_metadata', {}),
            )
        
        state["hana_response"] = response
        self.remember_memory(type="shortTerm_memory", state=state)
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
    
    def recall_memory(self, type: str, state: State):
        if type == "shortTerm":
            history = self.memory.shortTerm(mode="recall", state=state)
            return history
        
        elif type == "longTerm":
            pass
    
    def remember_memory(self, type: str, state:State):
        if type == "shortTerm":
            self.memory.shortTerm(mode="remember", state=state)
        elif type == "longTerm":
            pass
    

class Memory:
    def __init__(self, redis_conn, pg_con):
        self.redis_conn = redis_conn
        self.pg_con = pg_con
    
    def shortTerm(self, mode, state: State):
        if mode == "recall":
            history = self.redis_conn.get_history("Hana_ShortTerm")
            return history
        
        elif mode == "remember":
            conversant_message = state.get('messages')[0].content
            hana_response = state.get("hana_response").content
            self.redis_conn.list_history("Hana_ShortTerm", conversant_message)
            self.redis_conn.list_history("Hana_ShortTerm", hana_response)
            return "Hana Remembered Conversation"
    
    def longTerm(self, mode, state: State):
        if mode == "recall":
            pass
        elif mode == "remember":
            pass