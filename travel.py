import streamlit as st
from langchain_groq import ChatGroq
import os
import sqlite3
import requests

# -------- DATABASE SETUP --------
conn = sqlite3.connect("travel.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT,
    response TEXT
)
""")
conn.commit()

# -------- LLM SETUP --------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=1024,
)

# -------- TOOL 1: TRAVEL TOOL --------
def travel_tool(query):
    if "hyderabad" in query.lower():
        return """
📍 Top Places to Visit:
- Charminar
- Golconda Fort
- Ramoji Film City
- Hussain Sagar Lake

💰 Budget (2 Days):
- Stay: ₹1500/day
- Food: ₹500/day
- Travel: ₹500/day

📝 Tips:
- Use metro for cheap travel
- Visit Charminar early morning
"""
    return "⚠️ No travel data found for this location."


# -------- TOOL 2: WEB SEARCH (SIMULATED) --------
def web_search_tool(query):
    return f"""
🌐 Web Search Results (Simulated):

- Latest info about: {query}
- Example: news, general facts, trends

(Note: simulated for project)
"""


# -------- TOOL 3: WEATHER API (REAL) --------
def weather_tool(city):
    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        return "⚠️ Weather API key not set"

    url = f"http://api.weatherstack.com/current?access_key={api_key}&query={city}"

    try:
        response = requests.get(url)
        data = response.json()

        if "current" not in data:
            return "⚠️ City not found"

        temp = data["current"]["temperature"]
        desc = data["current"]["weather_descriptions"][0]

        return f"🌦 Weather in {city}: {temp}°C, {desc}"

    except:
        return "⚠️ Weather API failed"


# -------- UI --------
st.title("🌍 AI Travel Assistant (Multi-Tool Agent)")

user_input = st.text_input("Ask your travel question:")

# -------- AGENT LOGIC --------
if user_input:
    try:
        decision_prompt = f"""
You are an AI agent.

User Query: {user_input}

Decide:
- If weather related → WEATHER
- If travel/place planning → TRAVEL
- If general info/news → SEARCH
- Otherwise → CHAT

Respond ONLY one word:
WEATHER / TRAVEL / SEARCH / CHAT
"""

        decision = llm.invoke(decision_prompt).content.strip().upper()

        # -------- TOOL SELECTION --------
        if "WEATHER" in decision:
            result = weather_tool(user_input)
            st.success("🌦 Weather Tool Used")
            st.write(result)

        elif "TRAVEL" in decision:
            result = travel_tool(user_input)
            st.success("🧳 Travel Tool Used")
            st.write(result)

        elif "SEARCH" in decision:
            result = web_search_tool(user_input)
            st.success("🌐 Web Search Tool Used")
            st.write(result)

        else:
            response = llm.invoke(user_input)
            result = response.content
            st.success("🤖 AI Response")
            st.write(result)

        # -------- SAVE TO DATABASE --------
        cursor.execute(
            "INSERT INTO history (query, response) VALUES (?, ?)",
            (user_input, result)
        )
        conn.commit()

    except Exception as e:
        st.error(f"Error: {e}")


# -------- HISTORY SECTION --------
st.subheader("📜 Chat History")

if st.button("Show History"):
    rows = cursor.execute("SELECT * FROM history").fetchall()
    for row in rows:
        st.write(f"Q: {row[1]}")
        st.write(f"A: {row[2]}")
        st.write("---")