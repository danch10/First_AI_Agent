import os
import json
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
TASKS_FILE = "tasks.json"

# ─── Task functions ────────────────────────────────────────────────────────────

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def add_task(title):
    tasks = load_tasks()
    task = {"id": len(tasks) + 1, "title": title, "done": False}
    tasks.append(task)
    save_tasks(tasks)
    return f"Added task: '{title}'"

def get_tasks():
    tasks = load_tasks()
    if not tasks:
        return "Your task list is empty."
    lines = []
    for t in tasks:
        status = "✅" if t["done"] else "⬜"
        lines.append(f"{status} {t['id']}. {t['title']}")
    return "\n".join(lines)

def complete_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            save_tasks(tasks)
            return f"Marked '{t['title']}' as done."
    return f"No task found with id {task_id}."

# ─── Tool definitions (what Claude sees) ──────────────────────────────────────

tools = [
    {
        "name": "add_task",
        "description": "Add a new task to the user's task list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The task to add"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "get_tasks",
        "description": "Get all tasks from the user's task list.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a task as complete by its ID number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "The ID of the task to mark as done"}
            },
            "required": ["task_id"]
        }
    }
]

# ─── Tool router ──────────────────────────────────────────────────────────────

def run_tool(tool_name, tool_input):
    if tool_name == "add_task":
        return add_task(tool_input["title"])
    elif tool_name == "get_tasks":
        return get_tasks()
    elif tool_name == "complete_task":
        return complete_task(tool_input["task_id"])
    return "Unknown tool."

# ─── Claude with tool use ─────────────────────────────────────────────────────

def ask_claude(user_message):
    conversation_history.append({"role": "user", "content": user_message})

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system="You are a helpful personal productivity assistant. Be concise since your responses will be spoken aloud. You can manage the user's task list using your tools.",
        tools=tools,
        messages=conversation_history
    )

    # Tool use loop
    while response.stop_reason == "tool_use":
        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                print(f"🔧 Using tool: {block.name}({block.input})")
                result = run_tool(block.name, block.input)
                print(f"   Result: {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        # Add Claude's tool call + results to history
        conversation_history.append({"role": "assistant", "content": response.content})
        conversation_history.append({"role": "user", "content": tool_results})

        # Ask Claude again with the tool results
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system="You are a helpful personal productivity assistant. Be concise since your responses will be spoken aloud. You can manage the user's task list using your tools.",
            tools=tools,
            messages=conversation_history
        )

    # Final text reply
    reply = next(b.text for b in response.content if hasattr(b, "text"))
    conversation_history.append({"role": "assistant", "content": reply})
    return reply

# ─── Audio functions ───────────────────────────────────────────────────────────

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

def speak(text):
    import pyttsx3
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# ─── Main loop ────────────────────────────────────────────────────────────────

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