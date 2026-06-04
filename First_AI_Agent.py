import os
import anthropic
import openai
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from dotenv import load_dotenv

load_dotenv()

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

conversation_history = []

def record_audio(duration=5, sample_rate=44100):
    print("🎙️ Listening... (speak now)")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    write("input.wav", sample_rate, audio)
    print("✅ Got it!")

def transcribe_audio():
    with open("input.wav", "rb") as f:
        result = openai_client.audio.transcriptions.create(model="whisper-1", file=f)
    return result.text

def ask_claude(user_message):
    conversation_history.append({"role": "user", "content": user_message})
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system="You are a helpful personal productivity assistant. Be concise since your responses will be spoken aloud.",
        messages=conversation_history
    )
    reply = response.content[0].text
    conversation_history.append({"role": "assistant", "content": reply})
    return reply

def speak(text):
    # macOS: uses built-in 'say' command
    # Windows: uses PowerShell
    # Linux: uses espeak
    import platform
    system = platform.system()
    if system == "Darwin":
        os.system(f'say "{text}"')
    elif system == "Windows":
        os.system(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"')
    else:
        os.system(f'espeak "{text}"')

def main():
    print("🤖 Personal Agent ready! Press Enter to speak, type 'quit' to exit.\n")
    while True:
        user_input = input("Press Enter to speak (or type 'quit'): ")
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        record_audio(duration=5)
        text = transcribe_audio()
        print(f"You said: {text}")
        response = ask_claude(text)
        print(f"Agent: {response}\n")
        speak(response)

if __name__ == "__main__":
    main()