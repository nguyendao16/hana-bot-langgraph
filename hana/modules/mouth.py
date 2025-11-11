from kittentts import KittenTTS
import numpy as np
import sounddevice as sd

class Mouth:
    def __init__(self, voice: str = None, 
                       powerby: str = None):
        self.voice = voice
        self.larynx = KittenTTS(powerby)
    
    def __call__(self, state: dict):
        hana_response = state.get("hana_response")
        print("Hana is speaking...")
        if hasattr(hana_response, 'content'):
            text = hana_response.content
        else:
            text = str(hana_response)
        
        if not text or len(text.strip()) == 0:
            print("Warning: Empty response, skipping TTS")
            return state
            
        print(f"Speaking text: {text}")
        self.speaking(text)
        return state

    def speaking(self, text: str = "testing testing testing testing testing", 
                       samplerate: int = 24000):
        try:
            text = text.strip()
            if len(text) < 2:
                print(f"Text too short: '{text}'")
                return
            
            samples_list = self.larynx.generate(text, self.voice)
            samples = np.asarray(samples_list, dtype=np.float32)
            samples = np.clip(samples, -1.0, 1.0)
            sd.play(samples, samplerate)
            sd.wait()
        except Exception as e:
            print(f"TTS Error: {e}")
            print(f"Failed text: {text}")

if __name__ == "__main__":
    mouth = Mouth()
    mouth.speaking()