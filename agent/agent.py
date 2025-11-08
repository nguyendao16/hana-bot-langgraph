import redis
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import tools_condition, ToolNode
from functools import partial
from dotenv import load_dotenv
from os import getenv
from pathlib import Path
from .utils.state import State
from .utils.tools import rag_search
from .utils.nodes import chatbot,ToolNode,read_memory,write_memory

load_dotenv()
OLLAMA_HOST=getenv("OLLAMA_HOST")
REDIS_URL=getenv("REDIS_URL")
GOOGLE_API_KEY=getenv("GOOGLE_API_KEY")

async def create_graph(redis_client, pg_client):
    #---Initialize Model---
    llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY)
    
    current_dir = Path(__file__).parent
    prompt_path = current_dir / 'prompt_template.txt'
    with open(prompt_path, 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read()
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages")
    ])
    tools = [rag_search]
    llm_with_tools = prompt_template | llm.bind_tools(tools)

    #---Building Graph---
    graph_builder = StateGraph(State)
    graph_builder.add_node("read_memory", partial(read_memory, redis_client=redis_client))
    graph_builder.add_node("chatbot", partial(chatbot, llm_with_tools=llm_with_tools))
    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_node("write_memory", partial(write_memory, redis_client=redis_client))
    
    graph_builder.add_edge(START, "read_memory")
    graph_builder.add_edge("read_memory", "chatbot")
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot", 
        tools_condition, 
        {"tools": "tools", "__end__": "write_memory"}
    )
    graph_builder.add_edge("write_memory", END)
    graph = graph_builder.compile()
    return graph
