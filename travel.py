import streamlit as st
from langchain_groq import ChatGroq
import os
import requests

# -------- API KEY CHECK --------
if not os.getenv("GROQ_API_KEY"):
    st.error("❌ GROQ API Key missing")
    st.stop()

# -------- LLM SETUP --------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=1024,
)

# -------- HELPER: EXTRACT CITY --------
def extract_city(query):
    if "in" in query.lower():
        return query.lower().split("in")[-1].strip()
    return query.strip()

# -------- TOOL 1: TRAVEL (LLM BASED) --------
def travel_tool(query):
    prompt = f"""
You are a professional travel planner.

Create a realistic 2-day travel plan for: {query}

Include:
- Top tourist places
- Budget in INR (stay, food, transport)
- Best time to visit
- Travel tips
"""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception:
        return "⚠️ Travel service unavailable"

# -------- TOOL 2: WEATHER --------
def weather_tool(query):
    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        return "⚠️ Weather API key missing"

    city = extract_city(query)

    try:
        url = f"http://api.weatherstack.com/current?access_key={api_key}&query={city}"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return "⚠️ Weather service unavailable"

        data = res.json()

        if "current" not in data:
            return "⚠️ Invalid city name"

        temp = data["current"]["temperature"]
        desc = data["current"]["weather_descriptions"][0]

        return f"🌦 Weather in {city.title()}: {temp}°C, {desc}"

    except requests.exceptions.Timeout:
        return "⚠️ Weather API timeout"
    except Exception:
        return "⚠️ Weather service error"

# -------- TOOL 3: SEARCH (SIMULATED) --------
def web_search_tool(query):
    return f"""
🌐 Search Result:

- Information about: {query}
- Includes trends, general facts, and news

(Note: Simulated search tool for demo)
"""

# -------- UI --------
st.title("🌍 AI Travel Assistant (Final Version)")

user_input = st.text_input("Ask your question:")

# -------- EMPTY INPUT --------
if user_input and not user_input.strip():
    st.warning("⚠️ Please enter a valid query")
    st.stop()

# -------- RULE-BASED DECISION --------
def decide_tool(query):
    q = query.lower()

    if "weather" in q:
        return "weather"
    elif "trip" in q or "plan" in q or "travel" in q:
        return "travel"
    elif "news" in q or "latest" in q:
        return "search"
    else:
        return "chat"

# -------- MAIN LOGIC --------
if user_input:
    try:
        decision = decide_tool(user_input)

        if decision == "weather":
            result = weather_tool(user_input)
            st.success("🌦 Weather Tool Used")

        elif decision == "travel":
            result = travel_tool(user_input)
            st.success("🧳 Travel Tool Used")

        elif decision == "search":
            result = web_search_tool(user_input)
            st.success("🌐 Search Tool Used")

        else:
            try:
                response = llm.invoke(user_input)
                result = response.content
            except Exception:
                result = "⚠️ AI service temporarily unavailable"

            st.success("🤖 AI Response")

        st.write(result)

    except Exception:
        st.error("⚠️ Something went wrong. Please try again.")