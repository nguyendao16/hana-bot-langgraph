from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from .state import State

def extract_text_content(content):
    """
    Extract text content from AIMessage content.
    Handles both string format (OpenAI) and list format (Gemini).
    
    Args:
        content: Either a string or a list of dicts with format [{'type': 'text', 'text': '...'}]
    
    Returns:
        str: Extracted text content
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_content = ""
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_content += item.get("text", "")
        return text_content
    return str(content)

async def chatbot(state: State, llm_with_tools):
    response = await llm_with_tools.ainvoke({"messages": state["messages"]})
    response.content = extract_text_content(response.content)
    return {"messages": [response]}

class ToolNode:
    """A node that runs the tools requested in the last AIMessage."""
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}
    async def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = await self.tools_by_name[tool_call["name"]].ainvoke(
                tool_call["args"]
            )
        outputs.append(
            ToolMessage(
                content=tool_result,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

async def read_memory(state: State, redis_client):
    thread_id = state.get("thread_id")
    current_message = state.get("messages")
    history = await redis_client.get_history(thread_id)
    current_message.append(SystemMessage(content=f"Chat history: {history}"))
    return {"messages": current_message}

async def write_memory(state: State, redis_client, windows_length=10):
    thread_id = state.get("thread_id")
    user_message = state.get("messages")[0].content
    bot_message = state.get("messages")[-1].content
    await redis_client.list_history(thread_id, user_message, windows_length)
    await redis_client.list_history(thread_id, bot_message, windows_length)
    return {"bot_message": bot_message}
