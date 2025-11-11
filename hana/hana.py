from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from os import getenv
from .modules.state import State

load_dotenv()
OLLAMA_HOST=getenv("OLLAMA_HOST")

class Hana:
    def __init__(self, brain, ears, mouth):
        self.brain = brain
        self.ears = ears
        self.mouth = mouth
        self.hana = None

    def CraftingHana(self):
        if self.hana is not None:
            return self.hana
        
        print("Hana is loading... <3")
        #---Building Hana---
        graph_builder = StateGraph(State)
        graph_builder.add_node("Brain", self.brain)
        graph_builder.add_node("Ears", self.ears)
        graph_builder.add_node("Mouth", self.mouth)
        
        graph_builder.add_edge(START, "Ears")
        graph_builder.add_edge("Ears", "Brain")
        graph_builder.add_edge("Brain", "Mouth")
        graph_builder.add_edge("Mouth", END)
        Hana = graph_builder.compile()
        self.hana = Hana
        print("Done <3 <3 <3")
        return self.hana
    
    def AskHana(self):
        print("\n=== Starting Hana Execution ===\n")
        while True:
            try:
                input_state = {"messages": [], "conversant": "Futurio", "hana_response": ""}
                
                for output in self.hana.stream(input_state):
                    for node_name, node_output in output.items():
                        print(f"--- Node: {node_name} ---")
                        print(f"Output: {node_output}")
                        print()
                
                print("\n=== Conversation completed. Starting new conversation... ===\n")
                
            except KeyboardInterrupt:
                print("\n\n=== Hana is stopped ===")
                break
            except Exception as e:
                print(f"\nError occurred: {e}")
                print("=== Restarting conversation... ===\n")
                continue
