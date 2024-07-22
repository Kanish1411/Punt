from deepgram import Deepgram
import asyncio, json, os
import pyaudio
import wave
import numpy as np
import time
from openai import OpenAI

# Initialize the Deepgram client with your API key
dg = Deepgram("fe9cb1acb73d32204b6b8d3ed2e07175fd2e765f")
client = OpenAI(
        api_key="sk-None-BT7vYnLkVjjG571rNam4T3BlbkFJXuqsEcQfRYj15xYPIFIO",

    )

# Define options for transcription
options = {
    "model": "general",
    "tier": "enhanced"
}

SAMPLE_RATE = 16000  # Sample rate in Hz
CHUNK = 1024         # Number of frames per buffer
FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
CHANNELS = 1  
MAX_RECORDING_TIME = 20  # Maximum recording time in seconds
SILENCE_THRESHOLD = 1000  # RMS value below which audio is considered silence
SILENCE_DURATION = 2      # Duration of silence in seconds to stop recording

async def speechtosudio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print(f"Recording for up to {MAX_RECORDING_TIME} seconds or until silence is detected...")
    frames = []
    start_time = time.time()
    silence_start_time = None

    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        audio_data = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(np.square(audio_data))) 
        if rms < SILENCE_THRESHOLD:
            if silence_start_time is None:
                silence_start_time = time.time()
            elif time.time() - silence_start_time > SILENCE_DURATION:
                print("Silence detected. Stopping recording.")
                break
        else:
            silence_start_time = None  
        if time.time() - start_time > MAX_RECORDING_TIME:
            print("Maximum recording time reached. Stopping recording.")
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    output_file = "audio/output.wav"
    wf = wave.open(output_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"Recording saved to {output_file}")

async def Audiototext():
    audio_files = os.listdir("./audio")
    for audio_file in audio_files:
        audio_path = f"audio/{audio_file}"
        with open(audio_path, "rb") as file:
            src = {
                "buffer": file,
                "mimetype": "audio/wav"  
            }
            try:
                res = await dg.transcription.prerecorded(src, options)
                output_path = f"output/{audio_file[:-4]}.json"
                with open(output_path, "w") as output_file:
                    json.dump(res, output_file, indent=4)
                print(f"Transcription result saved to {output_path}")
            except Exception as e:
                print(f"Error processing {audio_file}: {e}")
    with open('output/output.json', 'r') as f:
        data = json.load(f)
        return(data["results"]["channels"][0]["alternatives"][0]["transcript"])

async def LLm(prompt):
    resp = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
    )
    print(resp['choices'][0]['message']["content"])
async def main():
    await speechtosudio()
    prompt=await Audiototext()
    await LLm(prompt)


if __name__ == "__main__":
    asyncio.run(main())
