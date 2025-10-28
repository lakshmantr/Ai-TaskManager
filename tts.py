from elevenlabs import ElevenLabs
import sounddevice as sd
import numpy as np
import os
from dotenv import load_dotenv
load_dotenv() 
client=ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
def audio_generator(text:str):
    audio_file=client.text_to_speech.convert(
        text=text,
        voice_id="pFZP5JQG7iQjIQuC4Bku",
        model_id="eleven_multilingual_v2",
        output_format="pcm_16000"
    )
    audio_data=(b"".join(audio_file))
    audio=np.frombuffer(audio_data,dtype=np.int16).astype(np.float32)
    audio/=32768.0
    sd.play(audio,samplerate=16000)
    sd.wait()