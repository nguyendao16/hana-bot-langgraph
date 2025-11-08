from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

class State(TypedDict):
    messages : Annotated[list[BaseMessage], add_messages]
    thread_id : str
    bot_message : str
