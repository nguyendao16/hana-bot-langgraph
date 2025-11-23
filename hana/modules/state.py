from typing_extensions import TypedDict

class State(TypedDict):
    messages : list
    conversant : str
    hana_response : str
    channel: str