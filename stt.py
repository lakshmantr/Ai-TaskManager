#The device index may vary use the code given below the get the index of your input device. 
#import sounddevice as sd
#print(sd.query_devices())
import sounddevice as sd
import io
import wave
from sarvamai import SarvamAI
import os
from dotenv import load_dotenv
load_dotenv()
def get_user_input():
    duration = 6 
    sample_rate = 44100
    print("Recording...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16',device=2)
    sd.wait()
    audio_data = io.BytesIO()
    wav = wave.open(audio_data, "wb")
    wav.setnchannels(1)
    wav.setframerate(sample_rate)
    wav.setsampwidth(2)
    wav.writeframes(audio.tobytes())
    wav.close()
    audio_data.seek(0)
    client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))
    response = client.speech_to_text.transcribe(
        file=audio_data,
        language_code="en-IN",
        model="saarika:v2.5"
    )
    transcript = response.transcript
    print(transcript)
    return transcript