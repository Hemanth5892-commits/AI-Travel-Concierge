import streamlit as st
from langchain_groq import ChatGroq
from langchain.tools import Tool
import os
import requests

# -------- LLM SETUP --------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=1024,
)

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


# -------- TOOL 2: WEATHER (REAL API + SAFE) --------
def weather_tool(query):
    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        return "⚠️ Weather API key missing"

    try:
        url = f"http://api.weatherstack.com/current?access_key={api_key}&query={query}"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return "⚠️ Weather service unavailable"

        data = res.json()

        if "current" not in data:
            return "⚠️ Invalid city name"

        temp = data["current"]["temperature"]
        desc = data["current"]["weather_descriptions"][0]

        return f"🌦 Weather in {query}: {temp}°C, {desc}"

    except requests.exceptions.Timeout:
        return "⚠️ Weather API timeout"

    except Exception:
        return "⚠️ Weather service error"


# -------- TOOL 3: WEB SEARCH --------
def web_search_tool(query):
    return f"""
🌐 Web Search Result:

- Information about: {query}
- Includes trends, news, and general facts
"""


# -------- LANGCHAIN TOOL DEFINITIONS --------
tools = [
    Tool(
        name="TravelTool",
        func=travel_tool,
        description="Use for travel planning queries"
    ),
    Tool(
        name="WeatherTool",
        func=weather_tool,
        description="Use for weather queries"
    ),
    Tool(
        name="SearchTool",
        func=web_search_tool,
        description="Use for general info or news"
    ),
]

# -------- UI --------
st.title("🌍 AI Travel Assistant (Final Version)")

user_input = st.text_input("Ask your question:")

# -------- EMPTY INPUT HANDLING --------
if user_input and not user_input.strip():
    st.warning("⚠️ Please enter a valid query")
    st.stop()

# -------- AGENT LOGIC --------
if user_input:
    try:
        decision_prompt = f"""
You are an intelligent agent.

User Query: {user_input}

Available Tools:
- TravelTool → travel planning
- WeatherTool → weather info
- SearchTool → general info

Respond ONLY:
TravelTool / WeatherTool / SearchTool / Chat
"""

        try:
            decision = llm.invoke(decision_prompt).content.strip()
        except Exception:
            decision = "Chat"

        # -------- TOOL EXECUTION --------
        if "WeatherTool" in decision:
            result = weather_tool(user_input)
            st.success("🌦 Weather Tool Used")

        elif "TravelTool" in decision:
            result = travel_tool(user_input)
            st.success("🧳 Travel Tool Used")

        elif "SearchTool" in decision:
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