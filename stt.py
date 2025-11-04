#The device index may vary use the code given below the get the index of your input device. 
#import sounddevice as sd
#print(sd.query_devices())
from sarvamai import SarvamAI
import pyaudio
import io
import wave
import os
from dotenv import load_dotenv
load_dotenv()
def get_user_input():
    audio=pyaudio.PyAudio()
    stream=audio.open(format=pyaudio.paInt16,
                  channels=1,
                  rate=44100,
                  input=True,
                  input_device_index=2,
                  frames_per_buffer=1024)
    frames=[]
    print("Recording...")
    for _ in range(0,int(44100/1024*6)):
        frames.append(stream.read(1024))
    stream.stop_stream()
    stream.close()
    audio.terminate()
    audio_data=io.BytesIO()
    wav=wave.open(audio_data,"wb")
    wav.setnchannels(1)
    wav.setframerate(44100)
    wav.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wav.writeframes(b"".join(frames))
    wav.close()
    audio_data.seek(0)
    client = SarvamAI(
        api_subscription_key=os.getenv("SARVAM_API_KEY"),
)
    response = client.speech_to_text.transcribe(
        file=audio_data,
        language_code="en-IN",
        model="saarika:v2.5"
)
    transcript = response.transcript
    print(transcript)
    return transcript