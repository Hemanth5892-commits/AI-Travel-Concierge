import os
from langchain_groq import ChatGroq
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -------- LLM --------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=512,
)

# -------- TRAVEL TOOL --------
def travel_tool(query):
    prompt = f"""
Create a short 2-day travel plan for: {query}
"""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception:
        return "Travel tool failed"


# -------- WEATHER TOOL --------
def weather_tool(query):
    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        return "Weather API key missing"

    try:
        url = f"http://api.weatherstack.com/current?access_key={api_key}&query={query}"
        res = requests.get(url)
        data = res.json()

        if "current" not in data:
            return "Invalid city"

        return f"{query}: {data['current']['temperature']}°C"

    except:
        return "Weather tool failed"


# -------- SEARCH TOOL --------
def web_search_tool(query):
    return f"Search result for: {query}"


# -------- TESTING --------
print("\n🔍 TESTING TOOLS...\n")

print("🧳 Travel Tool:")
print(travel_tool("Goa"))
print("-" * 50)

print("🌦 Weather Tool:")
print(weather_tool("Hyderabad"))
print("-" * 50)

print("🌐 Search Tool:")
print(web_search_tool("latest news India"))
print("-" * 50)

print("\n✅ Testing Completed\n")