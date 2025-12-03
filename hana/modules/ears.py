from RealtimeSTT import AudioToTextRecorder
from langchain_core.messages import HumanMessage
import logging

class Ears:
    def __init__(self, powerby: str = None):
        self.recorder = AudioToTextRecorder(model=powerby,
                                            device="cuda",
                                            gpu_device_index=0,
                                            compute_type="float32",
                                            level=logging.WARNING,
                                            )
    def __call__(self, state: dict):
        print("Hana is listening...")
        message = self.listening()
        state["messages"] = [HumanMessage(content=message)]
        return state

    def listening(self):
        input("Press Enter to start recording...")
        print("Press Enter again to stop recording... ")
        self.recorder.start()
        input()
        
        self.recorder.stop()
        text = self.recorder.text()
        return text.strip()