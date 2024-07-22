from flask import Flask, render_template, jsonify, request
import pyaudio
import numpy as np
import wave
import os
import json
import asyncio
from deepgram import Deepgram
from openai import OpenAI
import time
import google.generativeai as genai
from gtts import gTTS


app = Flask(__name__)

# Constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK = 1024
MAX_RECORDING_TIME = 20  # seconds
SILENCE_THRESHOLD = 100  # adjust as needed
SILENCE_DURATION = 3  # seconds

dg = Deepgram("fe9cb1acb73d32204b6b8d3ed2e07175fd2e765f")
client = OpenAI(api_key="sk-None-BT7vYnLkVjjG571rNam4T3BlbkFJXuqsEcQfRYj15xYPIFIO",)

genai.configure(api_key="AIzaSyA8VB9-nqcYc2_1HNWkH0WsSMpuwFnfaxs")  

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)


# Define options for transcription
options = {
    "model": "general",
    "tier": "enhanced"
}

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

async def Audiototext():
    audio_files = os.listdir("./audio")
    for audio_file in audio_files:
        audio_path = f"audio/{audio_file}"
        with open(audio_path, "rb") as file:
            src = {
                "buffer": file,
                "mimetype": "audio/wav"  # Correct MIME type for WAV files
            }
            try:
                res = await dg.transcription.prerecorded(src, options)
                return res["results"]["channels"][0]["alternatives"][0]["transcript"] 
            except Exception as e:
                print(f"Error processing {audio_file}: {e}")
        

async def LLm(prompt):
    # resp = client.chat.completions.create(
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": prompt,
    #         }
    #     ],
    #     model="gpt-3.5-turbo",
    # )
    # return resp['choices'][0]['message']["content"]
    try:
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(prompt)
        op = response.text.strip()
        return op
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return "error"

@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    text = request.json.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'})

    # Initialize gTTS
    tts = gTTS(text=text, lang='en')

    # Save audio to a file
    audio_file = os.path.join("audio", 'output.mp3')
    tts.save(audio_file)

    # Return the path to the generated audio file
    return send_file(audio_file, as_attachment=True, attachment_filename='output.mp3')

async def main():
    await speechtosudio()
    prompt = await Audiototext()
    return prompt

@app.route('/')
def home():
    return render_template('index.html', text="")

@app.route('/record_audio', methods=['POST'])
def record_audio():
    var = asyncio.run(main())
    return jsonify({'audio_text': var})

@app.route('/config_output', methods=['POST'])
def config_output():
    prompt = request.json.get('prompt')  # Get prompt from request data
    print(prompt)
    var = asyncio.run(LLm(prompt))
    print(var)
    if var !="error":
        return jsonify({'text': var})

if __name__ == '__main__':
    app.run(debug=True)
