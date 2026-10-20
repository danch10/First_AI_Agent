import os
import requests
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def search_web(query):
    results = tavily_client.search(query, max_results=3)
    if not results["results"]:
        return "No results found."
    lines = []
    for r in results["results"]:
        lines.append(f"- {r['title']}: {r['content'][:200]}")
    return "\n".join(lines)

def get_weather(city):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    if data.get("cod") != 200:
        return f"Couldn't get weather for {city}."
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    description = data["weather"][0]["description"]
    return f"{city}: {description}, {temp}°C (feels like {feels_like}°C)"

def get_news(topic):
    api_key = os.getenv("NEWS_API_KEY")
    url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&pageSize=3&apiKey={api_key}"
    response = requests.get(url)
    data = response.json()
    if data.get("status") != "ok":
        return f"Couldn't get news for {topic}."
    articles = data["articles"]
    if not articles:
        return f"No news found for {topic}."
    lines = []
    for a in articles:
        lines.append(f"- {a['title']} ({a['source']['name']})")
    return "\n".join(lines)