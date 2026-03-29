
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from langchain_groq import ChatGroq
import os
import requests

st.write("WEATHER:", os.getenv("WEATHER_API_KEY"))
st.write("RAPID:", os.getenv("RAPIDAPI_KEY"))
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
    words = query.strip().split()
    return words[-1]  # simple and more reliable than your old logic

# -------- TOOL 1: TRAVEL --------
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

# -------- TOOL 3: HOTEL (RAPIDAPI) --------
def hotel_tool(query):
    api_key = os.getenv("RAPIDAPI_KEY")

    if not api_key:
        return "⚠️ RapidAPI key missing"

    city = extract_city(query)

    url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }

    params = {
        "name": city,
        "locale": "en-gb"
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)

        if res.status_code != 200:
            return f"⚠️ API error: {res.status_code}"

        data = res.json()

        if not data:
            return "⚠️ No hotels found"

        result = f"🏨 Hotels in {city.title()}:\n\n"

        for place in data[:5]:
            name = place.get("name", "Unknown")
            region = place.get("region", "")
            dest_type = place.get("dest_type", "")

            result += f"• {name} ({region}) [{dest_type}]\n"

        return result

    except requests.exceptions.Timeout:
        return "⚠️ Hotel API timeout"
    except Exception as e:
        return f"⚠️ Hotel API error: {str(e)}"

# -------- TOOL 4: SEARCH --------
def web_search_tool(query):
    return f"""
🌐 Search Result:

- Information about: {query}
- Includes trends, general facts, and news

(Note: Simulated search tool for demo)
"""

# -------- UI --------
st.title("🌍 AI Travel Assistant")

user_input = st.text_input("Ask your question:")

# -------- EMPTY INPUT --------
if user_input and not user_input.strip():
    st.warning("⚠️ Please enter a valid query")
    st.stop()

# -------- DECISION LOGIC --------
def decide_tool(query):
    q = query.lower()

    if "weather" in q:
        return "weather"
    elif "hotel" in q or "stay" in q or "room" in q:
        return "hotel"
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

        elif decision == "hotel":
            result = hotel_tool(user_input)
            st.success("🏨 Hotel Tool Used")

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

    except Exception as e:
        st.error(f"⚠️ Something went wrong: {str(e)}")