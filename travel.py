from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from langchain_groq import ChatGroq
import os
import requests
import re
import sqlite3
import time
from datetime import datetime, timedelta
from duckduckgo_search import DDGS

# page setup
st.set_page_config(
    page_title="AI Travel Assistant",
    page_icon="🌍",
    layout="wide"
)

# css styling
st.markdown("""
<style>
    .user-bubble {
        background-color: #DCF8C6;
        padding: 10px 15px;
        border-radius: 15px 15px 0px 15px;
        margin: 5px 0;
        max-width: 70%;
        float: right;
        clear: both;
        color: #000 !important;
    }
    .assistant-bubble {
        background-color: #2a2a2a;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0px;
        margin: 5px 0;
        max-width: 70%;
        float: left;
        clear: both;
        color: #f0f0f0 !important;
    }
    .result-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 10px 0;
        color: #f0f0f0 !important;
    }
    .result-card b {
        color: #ffffff !important;
    }
    .clearfix { clear: both; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# check if api key is there otherwise stop
if not os.getenv("GROQ_API_KEY"):
    st.error("GROQ API Key missing please add it in .env file")
    st.stop()

# setup groq model
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=4096,
)

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("travel_searches.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool TEXT,
            query TEXT,
            city TEXT,
            result TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_search(tool, query, city, result):
    conn = sqlite3.connect("travel_searches.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO searches (tool, query, city, result, timestamp) VALUES (?, ?, ?, ?, ?)",
        (tool, query, city, result, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def get_recent_searches(limit=5):
    conn = sqlite3.connect("travel_searches.db")
    c = conn.cursor()
    c.execute(
        "SELECT tool, query, city, timestamp FROM searches ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    data = c.fetchall()
    conn.close()
    return data

def clear_searches():
    conn = sqlite3.connect("travel_searches.db")
    c = conn.cursor()
    c.execute("DELETE FROM searches")
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def extract_city(query):
    match = re.search(r"in ([A-Za-z\s]+)", query.lower())
    if match:
        return match.group(1).strip()
    return query.strip().split()[-1]

def extract_days(query):
    match = re.search(r"(\d+)\s*-?\s*day", query.lower())
    if match:
        d = int(match.group(1))
        if d > 7:
            d = 7  # cap at 7 days
        return d
    return 2  # default

def validate_input(query):
    """Basic input validation."""
    query = query.strip()
    if not query:
        return False, "Please type something first!"
    if len(query) < 3:
        return False, "Query is too short. Please be more specific."
    if len(query) > 500:
        return False, "Query is too long. Please keep it under 500 characters."
    return True, query

# ─────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────

def travel_tool(query):
    city = extract_city(query)
    days = extract_days(query)

    prompt = f"""
You are a professional travel planner.
Create a realistic {days}-day travel plan for {city.title()}.

For each day follow this exact format:

Day 1: [Theme for the day]
- Morning   (9AM-12PM) : [Activity] at [Place] — [short description]
- Afternoon (12PM-4PM) : [Activity] at [Place] — [short description]
- Evening   (4PM-8PM)  : [Activity] at [Place] — [short description]
- Dinner               : [Restaurant name] — [cuisine type, estimated cost in INR]

repeat for all {days} days

At the end include:
💰 Budget Estimate (INR) for {days} days:
- Stay    : ₹___
- Food    : ₹___
- Travel  : ₹___
- Total   : ₹___

🗓️ Best time to visit: [month/season]
💡 Travel tips: [3 useful tips]
"""
    try:
        res = llm.invoke(prompt)
        return res.content
    except Exception as e:
        return f"Travel tool error: {str(e)}"


@st.cache_data
def weather_tool(query):
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Weather API key not found in .env"

    city = extract_city(query)

    try:
        url = f"http://api.weatherstack.com/current?access_key={api_key}&query={city}"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return "Weather API not working right now."

        data = res.json()

        if "current" not in data or not data["current"]:
            return f"City '{city}' not found. Please check the spelling."

        temp = data["current"].get("temperature", "N/A")
        desc = data["current"].get("weather_descriptions", ["N/A"])[0]
        feels = data["current"].get("feelslike", "N/A")
        humidity = data["current"].get("humidity", "N/A")
        wind = data["current"].get("wind_speed", "N/A")

        return (
            f"🌦 Weather in {city.title()}:\n\n"
            f"🌡 Temperature : {temp}°C (Feels like {feels}°C)\n"
            f"☁ Condition   : {desc}\n"
            f"💧 Humidity    : {humidity}%\n"
            f"🌬 Wind Speed  : {wind} km/h"
        )

    except requests.exceptions.Timeout:
        return "Weather API took too long to respond."
    except Exception as e:
        return f"Weather error: {str(e)}"


def hotel_tool(query):
    api_key = os.getenv("RAPIDAPI_KEY")
    city = extract_city(query)

    if api_key:
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }

        try:
            dest_res = requests.get(
                "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination",
                headers=headers,
                params={"query": city},
                timeout=10
            )

            if dest_res.status_code == 429:
                raise Exception("quota done")
            if dest_res.status_code != 200:
                raise Exception("api error")

            dest_data = dest_res.json().get("data", [])
            if not dest_data:
                raise Exception("city not found in booking api")

            dest_id = dest_data[0].get("dest_id")
            dest_type = dest_data[0].get("search_type") or dest_data[0].get("dest_type") or "CITY"

            if not dest_id:
                raise Exception("no dest id")

            checkin = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
            checkout = (datetime.today() + timedelta(days=3)).strftime("%Y-%m-%d")

            params = {
                "dest_id": dest_id,
                "search_type": dest_type,
                "arrival_date": checkin,
                "departure_date": checkout,
                "adults": "1",
                "room_qty": "1",
                "sort_by": "popularity",
                "page_number": "1",
                "languagecode": "en-us",
                "currency_code": "INR"
            }

            hotel_res = None
            for i in range(3):
                try:
                    hotel_res = requests.get(
                        "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels",
                        headers=headers,
                        params=params,
                        timeout=25
                    )
                    if hotel_res.status_code == 429:
                        raise Exception("quota done")
                    break
                except requests.exceptions.Timeout:
                    if i == 2:
                        raise Exception("timeout after 3 tries")

            if hotel_res is None:
                raise Exception("no response")

            hotel_data = hotel_res.json()
            data_block = hotel_data.get("data", {})

            hotels = (
                data_block.get("result") or
                data_block.get("hotels") or
                data_block.get("data") or
                []
            )

            if not hotels:
                raise Exception("no hotels in response")

            output = f"🏨 Hotels in {city.title()}:\n\n"
            count = 0
            for h in hotels:
                if count >= 5:
                    break
                if not isinstance(h, dict):
                    continue
                prop = h.get("property", {})
                name = prop.get("name") or h.get("name") or h.get("hotel_name")
                rating = prop.get("reviewScore") or h.get("reviewScore") or h.get("review_score")
                price = prop.get("priceBreakdown", {}).get("grossPrice", {}).get("value") or h.get("min_total_price")

                if not name:
                    continue
                count += 1
                output += f"{count}. **{name}**\n"
                output += f"   ⭐ Rating : {rating if rating else 'N/A'}\n"
                output += f"   💰 Price  : {'₹' + str(int(float(price))) if price else 'N/A'}\n\n"

            if count == 0:
                raise Exception("could not parse hotel details")

            return output

        except Exception:
            pass  # fall through to AI fallback

    # AI fallback
    prompt = f"""
You are a hotel recommendation expert for Indian cities.

Suggest 5 realistic hotels in {city.title()} with the following format for each:

1. **[Hotel Name]**
   ⭐ Rating : [X.X out of 10]
   💰 Price  : ₹[approximate price per night]
   📍 Area   : [locality/area name]
   ✨ Known for: [one line description]

Include a mix of budget, mid-range and premium options.
Only suggest real, well-known hotels that actually exist in {city.title()}.
"""
    try:
        res = llm.invoke(prompt)
        return f"🏨 Hotels in {city.title()} (AI suggestions):\n\n" + res.content
    except Exception as e:
        return f"Hotel tool error: {str(e)}"


def itinerary_tool(query):
    city = extract_city(query)
    days = extract_days(query)

    prompt = f"""
You are an expert travel planner creating a detailed itinerary.
Create a {days}-day itinerary for {city.title()}.

For each day follow this exact format:

Day 1: [Theme for the day]
- Morning   (9AM-12PM) : [Activity] at [Place] — [short description]
- Afternoon (12PM-4PM) : [Activity] at [Place] — [short description]
- Evening   (4PM-8PM)  : [Activity] at [Place] — [short description]
- Dinner               : [Restaurant name] — [cuisine type, estimated cost in INR]

repeat for all {days} days

At the end include:
💰 Estimated Total Budget (INR):
- Stay    : ₹___
- Food    : ₹___
- Travel  : ₹___
- Entry   : ₹___
- Total   : ₹___

🧳 Packing Tips: [3 useful tips]
⚠️ Important Notes: [2 must-know tips for this city]
"""
    try:
        res = llm.invoke(prompt)
        return res.content
    except Exception as e:
        return f"Itinerary error: {str(e)}"


def web_search_tool(query):
    """Real web search using DuckDuckGo — no API key required."""
    try:
        time.sleep(1)  # small delay to avoid rate limiting
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=4):
                results.append(r)

        if not results:
            return "No results found for your query. Try rephrasing it."

        output = f"🌐 Search Results for: **{query}**\n\n"
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body  = r.get("body", "No description")
            href  = r.get("href", "")
            output += f"{i}. **{title}**\n"
            output += f"   {body[:200]}...\n"
            output += f"   🔗 {href}\n\n"

        return output

    except Exception as e:
        return f"Search error: {str(e)}\n\nTip: Try again in a moment — DuckDuckGo sometimes rate-limits requests."


# ─────────────────────────────────────────────
# TOOL ROUTER
# ─────────────────────────────────────────────

def decide_tool(query):
    q = query.lower()
    if any(word in q for word in ["weather", "temperature", "climate", "forecast"]):
        return "weather"
    elif any(word in q for word in ["hotel", "stay", "room", "accommodation", "hostel", "resort"]):
        return "hotel"
    elif any(word in q for word in ["itinerary", "schedule", "day by day", "daywise", "day-by-day"]):
        return "itinerary"
    elif any(word in q for word in ["trip", "plan", "travel", "visit", "tour"]):
        return "travel"
    elif any(word in q for word in ["news", "latest", "search", "find", "what is", "who is",
                                     "when did", "how to", "tell me about", "information on"]):
        return "search"
    else:
        return "chat"


# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────

def build_export_text(chat_history):
    lines = []
    lines.append("=" * 50)
    lines.append("   AI TRAVEL ASSISTANT - CHAT EXPORT")
    lines.append(f"   Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 50 + "\n")
    for msg in chat_history:
        role = "You" if msg["role"] == "user" else "Assistant"
        lines.append(f"[{role}]\n{msg['content']}\n")
        lines.append("-" * 40)
    return "\n".join(lines)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

st.title("🌍 AI Travel Assistant")
st.caption("Ask me about hotels, weather, itineraries, travel plans, or search the web!")

# sidebar
with st.sidebar:
    st.header("🕘 Recent Searches")
    recent = get_recent_searches()
    if recent:
        for row in recent:
            tool, query, city, timestamp = row
            st.markdown(f"**{tool.upper()}** — {city or query}")
            st.caption(f"🕒 {timestamp}")
            st.divider()
    else:
        st.info("No searches yet.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear History"):
            clear_searches()
            st.success("Cleared!")
            st.rerun()
    with col2:
        if st.button("🧹 Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    st.divider()
    st.subheader("📥 Export Chat")
    if st.session_state.chat_history:
        txt = build_export_text(st.session_state.chat_history)
        st.download_button(
            label="⬇️ Download as TXT",
            data=txt,
            file_name=f"travel_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.info("No chat to export yet.")

    st.divider()
    st.caption("💡 Try: 'Search what is the Eiffel Tower' or 'latest news about Goa tourism'")

# chat messages
chat_container = st.container()
with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-bubble">🧑 {msg["content"]}</div>'
                f'<div class="clearfix"></div>',
                unsafe_allow_html=True
            )
        else:
            tool = msg.get("tool", "chat")
            emojis = {
                "weather": "🌦",
                "hotel": "🏨",
                "itinerary": "🗓️",
                "travel": "🧳",
                "search": "🌐",
                "chat": "🤖"
            }
            emoji = emojis.get(tool, "🤖")
            content = msg["content"].replace("\n", "<br>")
            st.markdown(
                f'<div class="result-card"><b>{emoji} {tool.upper()}</b><br><br>{content}</div>',
                unsafe_allow_html=True
            )

# input bar
st.divider()
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "message",
            placeholder="e.g. Hotels in Goa / 3 day itinerary in Manali / Search what is Taj Mahal",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("Send 🚀", use_container_width=True)

# main logic
if submitted:
    valid, result_or_error = validate_input(user_input)

    if not valid:
        st.warning(result_or_error)
    else:
        clean_input = result_or_error

        st.session_state.chat_history.append({
            "role": "user",
            "content": clean_input
        })

        tool_to_use = decide_tool(clean_input)
        city = extract_city(clean_input)

        with st.spinner("Thinking..."):
            if tool_to_use == "weather":
                result = weather_tool(clean_input)
                save_search("weather", clean_input, city, result)

            elif tool_to_use == "hotel":
                result = hotel_tool(clean_input)
                save_search("hotel", clean_input, city, result)

            elif tool_to_use == "itinerary":
                result = itinerary_tool(clean_input)
                save_search("itinerary", clean_input, city, result)

            elif tool_to_use == "travel":
                result = travel_tool(clean_input)
                save_search("travel", clean_input, city, result)

            elif tool_to_use == "search":
                result = web_search_tool(clean_input)
                save_search("search", clean_input, clean_input, result)

            else:
                try:
                    response = llm.invoke(clean_input)
                    result = response.content
                except Exception as e:
                    result = f"AI error: {str(e)}"
                save_search("chat", clean_input, None, result)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result,
            "tool": tool_to_use
        })

        st.rerun()