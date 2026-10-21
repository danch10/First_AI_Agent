import os
import json
import anthropic
import openai
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from dotenv import load_dotenv
from database import save_conversation_summary, save_memory,load_memories
from web_tools import search_web, get_weather, get_news
from google_tools import get_emails, send_email,get_calendar_events, create_calendar_event
from aoutonomous import run_autonomous_task

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
    for i, task in enumerate(tasks, start=1):
        task["id"] = i
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def search_tasks(keyword):
    tasks = load_tasks()
    lines = []
    for t in tasks:
        if keyword.lower() in t["title"].lower():
            lines.append(f"{t['id']}. {t['title']}")
    if not lines:
        return f"No tasks found matching '{keyword}'."
    return "\n".join(lines)

def get_tasks():
    tasks = load_tasks()
    if not tasks:
        return "Your task list is empty."
    lines = []
    for t in tasks:
        status = "⬜"
        lines.append(f"{status} {t['id']}. {t['title']}")
    return "\n".join(lines)

def add_task(title):
    tasks = load_tasks()
    task = {"id": len(tasks) + 1, "title": title, "done": False}
    tasks.append(task)
    save_tasks(tasks)
    return f"Added task: '{title}'"

def delete_task(title):
    tasks = load_tasks()
    task = next((t for t in tasks if t.get("title") == title), None)
    if not task:
        return f"Didn't find the task: '{title}'"
    tasks.remove(task)
    save_tasks(tasks)
    return f"Deleted task: '{title}'"

def complete_tasks(task_names):
    tasks = load_tasks()
    titles = [t["title"] for t in tasks if t["title"] in task_names]
    if not titles:
        return "No matching tasks found."
    tasks = [t for t in tasks if t["title"] not in task_names]
    save_tasks(tasks)
    return f"Completed and removed: {', '.join(titles)}"

def remember(category, content):
    save_memory(category, content)
    return f"Got it, I'll remember that: [{category}] {content}"

def recall():
    memories = load_memories()
    if not memories:
        return "I don't have any memories yet."
    return memories

def summarise_and_save():
    if not conversation_history:
        return

    # Build a fresh summary request — don't use conversation_history directly
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system="You are a helpful assistant that summarises conversations.",
        messages=[
            {
                "role": "user",
                "content": f"Please summarise this conversation in 2-3 sentences. Focus on what the user did and any important information shared.\n\n{str(conversation_history)}"
            }
        ]
    )

    summary = response.content[0].text
    save_conversation_summary(summary)
    print(f"📝 Session saved: {summary}")

# ─── Tool definitions (what Claude sees) ──────────────────────────────────────

tools = [
    {
        "name": "search_tasks",
        "description": "Get all tasks from the user's task list that have the same keyword.",
        "input_schema": {
            "type": "object",
            "properties": {"keyword": {"type": "string", "description": "The keyword to search for"}
        },
        "required": ["keyword"]
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
        "name": "delete_task",
        "description": "Delete a required task from the user's task list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The task to add"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "complete_tasks",
        "description": "Complete and remove one or more tasks by their titles.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of task names to complete"
                }
            },
            "required": ["task_names"]
        }
    },
    {
        "name": "remember",
        "description": "Save something important to memory for future sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category of the memory e.g. 'personal', 'preference', 'work'"},
                "content": {"type": "string", "description": "The thing to remember"}
            },
            "required": ["category", "content"]
        }
    },
    {
        "name": "recall",
        "description": "Recall everything stored in memory about the user.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "summarise_and_save",
        "description": "Summarize and save the conversation history.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
{
    "name": "search_web",
    "description": "Search the internet for current information on any topic.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"}
        },
        "required": ["query"]
    }
},
{
    "name": "get_weather",
    "description": "Get current weather for a city.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "The city name"}
        },
        "required": ["city"]
    }
},
{
    "name": "get_news",
    "description": "Get latest news headlines for a topic.",
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "The news topic"}
        },
        "required": ["topic"]
    }
},
{
    "name": "get_emails",
    "description": "Get all emails for number of results asked for.",
    "input_schema": {
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "The maximum number of results"}
        },
        "required": ["max_results"]
    }
},
    {
        "name": "send_email",
        "description": "Send an email based on the information given.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"}
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "get_calendar_events",
        "description": "Get all calendar events for a topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {"type": "integer", "description": "Days ahead"}
            },
            "required": ["days_ahead"]
        }
    },
    {
        "name": "create_calendar_event",
        "description": "Create a calendar event for a topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The calendar event title"},
                "date": {"type": "string", "description": "The calendar event date"},
                "time": {"type": "string", "description": "The calendar event time"},
                "duration_hours": {"type": "integer", "description": "The calendar event duration hours"}
            },
            "required": ["title", "date", "time", "duration_hours"]
        }
    }
]

# ─── Tool router ──────────────────────────────────────────────────────────────

def run_tool(tool_name, tool_input):
    tool_map = {
        "search_tasks": lambda: search_tasks(tool_input["keyword"]),
        "get_tasks": lambda: get_tasks(),
        "add_task": lambda: add_task(tool_input["title"]),
        "complete_tasks": lambda: complete_tasks(tool_input["task_names"]),
        "delete_task": lambda: delete_task(tool_input["title"]),
        "remember": lambda: remember(tool_input["category"], tool_input["content"]),
        "recall": lambda: recall(),
        "summarise_and_save": lambda: summarise_and_save(),
        "search_web": lambda: search_web(tool_input["query"]),
        "get_weather": lambda: get_weather(tool_input["city"]),
        "get_news": lambda: get_news(tool_input["topic"]),
        "get_emails": lambda: get_emails(tool_input["max_results"]),
        "send_email": lambda: send_email(tool_input["to"], tool_input["subject"], tool_input["body"]),
        "get_calendar_events": lambda: get_calendar_events(tool_input["days_ahead"]),
        "create_calendar_event": lambda: create_calendar_event(tool_input["title"], tool_input["date"], tool_input["time"], tool_input["duration_hours"]),
    }
    tool_fn = tool_map.get(tool_name)
    if tool_fn:
        return tool_fn()
    return "Unknown tool."
# ─── Claude with tool use ─────────────────────────────────────────────────────

def ask_claude(user_message):
    from database import load_memories
    memories = load_memories()

    system_prompt = "You are a helpful personal productivity assistant. Be concise since your responses will be spoken aloud. You can manage the user's task list using your tools."

    if memories:
        system_prompt += f"\n\nWhat you remember about the user:\n{memories}"

    conversation_history.append({"role": "user", "content": user_message})

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system_prompt,
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

        conversation_history.append({"role": "assistant", "content": response.content})
        conversation_history.append({"role": "user", "content": tool_results})

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            tools=tools,
            messages=conversation_history
        )

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
        user_input = input("Press Enter to speak, type 'auto' for autonomous task, or 'quit': ")

        if user_input.lower() == 'auto':
            goal = input("What's the goal? → ")
            result = run_autonomous_task(goal, tools, run_tool, anthropic_client)
            conversation_history.append({"role": "user", "content": goal})
            conversation_history.append({"role": "assistant", "content": result})
            print(f"\n📋 Result:\n{result}\n")
            speak(result)
            continue
        if user_input.lower() == 'quit':
            summarise_and_save()
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