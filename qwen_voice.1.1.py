#!/usr/bin/env python
# coding: utf-8

import os
import queue
import threading
import sys
from datetime import datetime
import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
import mlx.core as mx
import mlx_audio.tts as mlx_tts
import mlx_audio.stt as mlx_stt
from mlx_audio.tts.generate import generate_audio
import socket  # <-- Added for UDP network listening

class QwenVoiceAssistant:
    """Encapsulates the ASR, LLM, and TTS pipeline for a local voice assistant. """
    def __init__(self, stt_path, tts_path, api_base):
        print("=== Initializing Voice Pipeline ===")
        
        # Load models as instance attributes
        self.stt_model = mlx_stt.load_model(stt_path)
        self.tts_model = mlx_tts.load_model(tts_path)
        
        # Initialize OpenAI/oMLX client
        self.client = OpenAI(
            base_url=api_base,  
            api_key=os.environ.get("OMLX_API_KEY", "omlx-c8bz4coj7tamktlg")
        )

        # Inter-thread communication
        self.text_synthesis_queue = queue.Queue()
        self.current_ref_text = ""
        
        # Constants
        self.TTS_SAMPLE_RATE = 24000
        self.MIC_SAMPLE_RATE = 16000

    def record_mic_input(self, output_file="user_voice.wav", duration=5):
        """Records user audio input."""
        print(f"\n LISTENING ({duration}s)... Speak clear coding prompts.")
        recording = sd.rec(int(duration * self.MIC_SAMPLE_RATE), 
                           samplerate=self.MIC_SAMPLE_RATE, 
                           channels=1, dtype='int16')
        sd.wait()
        sf.write(output_file, recording, self.MIC_SAMPLE_RATE)
        print("Recording stopped.")
        return output_file

    def process_stt(self, audio_path):
        """Converts speech to text using the local MLX ASR model."""
        try:
            text_pieces = []
            print("🧠 Decoding speech...")
            for text_chunk in self.stt_model.generate(audio_path, language="English", stream=True):
                print(text_chunk.text, end="", flush=True)
                text_pieces.append(text_chunk.text)
            print()
            return "".join(text_pieces).strip()
        except Exception as e:
            print(f"\nSTT Processing Error: {e}")
            return ""

    def _fetch_llm_stream(self, prompt):
        """Worker method to fetch LLM response and buffer into phrases."""
        print(" Querying local Qwen2.5-Coder engine...")
        
        now = datetime.now()
        current_date = now.strftime("%A, %B %d, %Y")
        current_time = now.strftime("%I:%M %p")
        
        system_instruction = (
            "You are a concise voice assistant. Keep answers short and concise. strictly conversational. "
            f"Temporal Awareness Anchor: Today's date is {current_date}, and the local time is {current_time}."
        )
        
        try:
            stream = self.client.chat.completions.create(
                model="Qwen2.5-Coder-7B-Instruct-MLX-8bit", 
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                stream=True,  
                temperature=0.2
            )

            phrase_buffer = ""
            delimiters = (".", "!", "?", "\n")

            for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    print(token, end="", flush=True)  
                    phrase_buffer += token

                    # Buffer slightly more text to reduce per-segment synthesis overhead
                    if any(delim in token for delim in delimiters) and len(phrase_buffer) > 25:
                        clean_phrase = phrase_buffer.strip().replace("`", "").replace("*", "")
                        self.text_synthesis_queue.put(clean_phrase)
                        phrase_buffer = ""

            if phrase_buffer.strip():
                self.text_synthesis_queue.put(phrase_buffer.strip())

        except Exception as e:
            print(f"\noMLX Connection Error: {e}")
        finally:
            self.text_synthesis_queue.put(None)

    def _voice_synthesis_consumer(self):
        """Streams audio chunks to speakers on the main thread."""
        # Using 24k natively; blocksize 1024 offers a better balance for responsiveness
        with sd.OutputStream(samplerate=self.TTS_SAMPLE_RATE, 
                             channels=1, 
                             dtype='float32',
                             blocksize=1024,
                             latency='high') as stream:
            while True:
                text_payload = self.text_synthesis_queue.get()
                if text_payload is None:  
                    break
                try:
                    audio_generator = generate_audio(
                        model=self.tts_model, 
                        text=text_payload,
                        ref_audio="./user_voice.wav",
                        ref_text=self.current_ref_text,
                        stream=True
                    )
                    for chunk in audio_generator:
                        if isinstance(chunk, mx.array):
                            mx.eval(chunk) # Ensure GPU compute is complete before playback
                            chunk = np.array(chunk)
                        stream.write(chunk)
                except Exception as e:
                    print(f"\nReal-time TTS failed on segment [{text_payload}]: {e}")
                self.text_synthesis_queue.task_done()

    def run_execution_cycle(self):
        """Orchestrates a single recording-processing-response cycle."""
        audio_path = self.record_mic_input()
        prompt = self.process_stt(audio_path)

        if not prompt:
            print("STT returned empty buffer. Aborting cycle.")
            return

        self.current_ref_text = prompt # Save prompt for high-speed speaker embedding
        print(f"\n👤 Decoded Prompt: \"{prompt}\"")

        llm_worker = threading.Thread(target=self._fetch_llm_stream, args=(prompt,))
        llm_worker.start()
        
        self._voice_synthesis_consumer()
        llm_worker.join()
        print("\n\n Execution cycle finished cleanly.")

def main():
    LOCAL_STT = "/Users/Admin/.omlx/models/mlx-community/Qwen3-ASR-0.6B-8bit"
    LOCAL_TTS = "/Users/Admin/.omlx/models/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-4bit"
    LOCAL_LLM = "http://127.0.0.1:8000/v1"
    assistant = QwenVoiceAssistant(LOCAL_STT, LOCAL_TTS, LOCAL_LLM)
    
    # Network Configuration
    UDP_IP = "127.0.0.1"  # Listen only on the local loopback interface
    UDP_PORT = 9999       # Dedicate a specific port for the trigger
    
    # Initialize the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    
    print(f"\n🚀 Voice Engine Isolated. Running securely as user: {os.getlogin()}")
    print(f"Awaiting network trigger on {UDP_IP}:{UDP_PORT}... [Ctrl+C to exit]")
    
    try:
        while True:
            # This line completely blocks execution, consuming 0% CPU until a packet arrives
            data, addr = sock.recvfrom(1024) 
            
            # Simple validation check on the payload
            if data == b"TRIGGER":
                print(f"\n[Network Trigger Received from {addr[0]}:{addr[1]}] Initiating cycle...")
                assistant.run_execution_cycle()
                print("\n Ready. Awaiting next network trigger...")
                
    except KeyboardInterrupt:
        print("\nExiting Voice Assistant. Goodbye!")
    finally:
        sock.close()

if __name__ == "__main__":
    main()