from .state import State

def ChannelCheck(state: State):
    """
    Expect state contains: {"channel": "voice"|"text", "payload": ...}
    Normalize to state["text_input"] for downstream Brain.
    """
    ch = state.get("channel")
    if ch == "voice":
        state["route"] = "voice"
    else:
        state["route"] = "text"
    return state

def OutputRouter(state: State):
    ch = state.get("channel")
    if ch == "voice":
        return "voice"
    else:
        return "text"