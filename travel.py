import streamlit as st
from langchain_groq import ChatGroq
import os
import requests

# -------- LLM SETUP --------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=2048,
)

# -------- TOOL 1: TRAVEL (DYNAMIC - NOT FAKE) --------
def travel_tool(query):
    prompt = f"""
You are a professional travel planner.

Create a realistic 2-day travel plan for: {query}

Include:
1. Top tourist places (specific to location)
2. Approx budget in INR (stay, food, transport)
3. Best time to visit
4. Travel tips

Keep it clear, structured, and practical.
"""
    response = llm.invoke(prompt)
    return response.content

# -------- TOOL 2: WEATHER (REAL API) --------
def weather_tool(query):
    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        return "⚠️ Weather API key not set"

    url = f"http://api.weatherstack.com/current?access_key={api_key}&query={query}"

    try:
        res = requests.get(url)
        data = res.json()

        if "current" not in data:
            return "⚠️ City not found"

        temp = data["current"]["temperature"]
        desc = data["current"]["weather_descriptions"][0]

        return f"🌦 Weather in {query}: {temp}°C, {desc}"

    except:
        return "⚠️ Weather API failed"

# -------- TOOL 3: WEB SEARCH (SIMULATED) --------
def web_search_tool(query):
    return f"""
🌐 Web Search Result:

- Information about: {query}
- Includes trends, news, and general facts

(Note: simulated search)
"""

# -------- UI --------
st.title("🌍 AI Travel Assistant (Final Version)")

user_input = st.text_input("Ask your travel question:")

# -------- AGENT LOGIC --------
if user_input:
    try:
        decision_prompt = f"""
You are a strict classifier.

User Query: {user_input}

Classify into ONE:
WEATHER / TRAVEL / SEARCH / CHAT

Respond ONLY one word.
"""

        decision = llm.invoke(decision_prompt).content.strip().upper()

        # -------- SAFE DECISION --------
        if "WEATHER" in decision:
            result = weather_tool(user_input)
            st.success("🌦 Weather Tool Used")

        elif "TRAVEL" in decision:
            result = travel_tool(user_input)
            st.success("🧳 Travel Tool Used")

        elif "SEARCH" in decision:
            result = web_search_tool(user_input)
            st.success("🌐 Web Search Tool Used")

        else:
            response = llm.invoke(user_input)
            result = response.content
            st.success("🤖 AI Response")

        st.write(result)

    except Exception as e:
        st.error(f"Error: {e}")