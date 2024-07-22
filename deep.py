import asyncio
import websockets
import json
import pyaudio
import time

DEEPGRAM_API_KEY = "fe9cb1acb73d32204b6b8d3ed2e07175fd2e765f"
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Deepgram's default sample rate
CHUNK = 1024
TIME_LIMIT = 5  # Duration in seconds

async def transcribe_audio():
    uri = "wss://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}"
    }
    
    audio = pyaudio.PyAudio()
    
    # Open the audio stream
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    
    start_time = time.time()
    
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        try:
            # Send audio data while time limit is not exceeded
            while True:
                if time.time() - start_time > TIME_LIMIT:
                    break
                
                data = stream.read(CHUNK, exception_on_overflow=False)
                if not data:
                    break
                
                await websocket.send(data)
        
        except Exception as e:
            print(f"Error while sending data: {e}")
        
        finally:
            # Stop and close the audio stream
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            print("Audio stream closed.")
            
            # Wait for any remaining messages from Deepgram
            try:
                while True:
                    response = await websocket.recv()
                    print(f"Received: {response}")
                    # Check for termination message or end of data
                    if "message" in json.loads(response):
                        print("Received final message.")
                        break
            except websockets.ConnectionClosed:
                print("WebSocket connection closed.")
            except Exception as e:
                print(f"Error receiving message: {e}")
            
            # Close the WebSocket connection properly
            try:
                await websocket.close()
                print("WebSocket connection closed.")
            except Exception as e:
                print(f"Error closing WebSocket: {e}")

asyncio.run(transcribe_audio())




# import asyncio
# import websockets
# import json
# import os
# import pyaudio
# import time

# DEEPGRAM_API_KEY = "fe9cb1acb73d32204b6b8d3ed2e07175fd2e765f"
# AUDIO_FILE_PATH = "audio\otuput.m4a"  # Use raw string for Windows paths
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 16000  # Deepgram's default sample rate
# CHUNK = 1024
# TIME_LIMIT = 5

# async def transcribe_audio():
#     uri = "wss://api.deepgram.com/v1/listen"
#     headers = {
#         "Authorization": f"Token {DEEPGRAM_API_KEY}"
#     }
#     audio = pyaudio.PyAudio()
    
#     # Open the audio stream
#     stream = audio.open(format=FORMAT,
#                         channels=CHANNELS,
#                         rate=RATE,
#                         input=True,
#                         frames_per_buffer=CHUNK)
#     start_time = time.time()
#     async with websockets.connect(uri, extra_headers=headers) as websocket:
#         with open(AUDIO_FILE_PATH, 'rb') as audio_file:
#             while True:
#                 if time.time() - start_time > TIME_LIMIT:
#                     break
#                 data = stream.read(CHUNK, exception_on_overflow=False)
#                 print(data)
#                 if not data:
#                     break
#                 await websocket.send(data)
#         print("sukjdjgsydfgyu")
#         while True:
#             response = await websocket.recv()
#             print(response)
#             if "message" in json.loads(response):
#                 break

# asyncio.run(transcribe_audio())

