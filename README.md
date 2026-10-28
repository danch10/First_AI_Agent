# Personal AI Agent

A fully functional personal AI agent built from scratch in Python. Voice-controlled, memory-enabled, and connected to real-world services.

## What this agent can do

- 🎙️ Listen to your voice and respond out loud
- 📋 Manage a task list by voice — add, complete, delete, search
- 🧠 Remember facts about you across sessions using a MySQL database
- 📝 Summarise every conversation and save it automatically
- 🌐 Search the web in real time using Tavily
- 🌤️ Get live weather for any city
- 📰 Fetch latest news by topic
- 📅 Read and create Google Calendar events by voice
- 📧 Read and send Gmail emails by voice
- 🤖 Run autonomous multi-step tasks without guidance
- 💬 Accessible via Telegram from anywhere

## Project structure

```
├── First_AI_Agent.py      # Main agent — voice loop, tool use, Claude API
├── autonomous.py          # Autonomous ReAct loop
├── database.py            # MySQL connection and memory functions
├── web_tools.py           # Web search, weather, news tools
├── google_tools.py        # Google Calendar and Gmail integration
├── telegram_bot.py        # Telegram bot interface
├── .env                   # API keys (not in GitHub)
├── .gitignore
└── requirements.txt
```

## Tech stack

| Layer | Technology |
| --- | --- |
| AI brain | Claude API (Anthropic) |
| Speech to text | Whisper (OpenAI) |
| Text to speech | pyttsx3 |
| Database | MySQL in Docker |
| Web search | Tavily |
| Weather | OpenWeatherMap API |
| News | NewsAPI |
| Google services | Google Calendar + Gmail API |
| Messaging interface | Telegram Bot API |
| Language | Python 3.12 |

## Setup instructions

### 1. Clone the repository
```bash
git clone https://github.com/danch10/First_AI_Agent.git
cd First_AI_Agent
```

### 2. Create a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
OPENWEATHER_API_KEY=your_openweather_key
NEWS_API_KEY=your_newsapi_key
TELEGRAM_BOT_TOKEN=your_telegram_token
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=agentpass
DB_NAME=agentdb
```

### 5. Start the MySQL database
```bash
docker run --name agent-db -e MYSQL_ROOT_PASSWORD=agentpass -e MYSQL_DATABASE=agentdb -p 3306:3306 -d mysql:8
```

### 6. Set up the database tables
```bash
python database.py
```

### 7. Add Google credentials
- Create a project in Google Cloud Console
- Enable Calendar and Gmail APIs
- Download OAuth credentials as `credentials.json` and place in project root
- Add yourself as a test user in the OAuth consent screen

### 8. Run the agent

**Voice mode:**
```bash
python First_AI_Agent.py
```

**Telegram mode:**
```bash
python telegram_bot.py
```

## API keys required

| Key | Where to get it |
| --- | --- |
| Anthropic | console.anthropic.com |
| OpenAI | platform.openai.com |
| Tavily | app.tavily.com |
| OpenWeatherMap | openweathermap.org/api |
| NewsAPI | newsapi.org |
| Telegram | @BotFather on Telegram |
| Google | console.cloud.google.com |
