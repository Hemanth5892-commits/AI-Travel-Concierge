from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from langchain_groq import ChatGroq
import os
import requests
import re
import sqlite3
from datetime import datetime, timedelta

# check if groq api key is there
if not os.getenv("GROQ_API_KEY"):
    st.error("GROQ API Key is missing!")
    st.stop()

# setup the AI model
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=2048,
)

# database functions
def init_db():
    con = sqlite3.connect("travel_searches.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool TEXT,
            query TEXT,
            city TEXT,
            result TEXT,
            timestamp TEXT
        )
    """)
    con.commit()
    con.close()

def save_search(tool, query, city, result):
    con = sqlite3.connect("travel_searches.db")
    cur = con.cursor()
    cur.execute("INSERT INTO searches (tool, query, city, result, timestamp) VALUES (?, ?, ?, ?, ?)",
                (tool, query, city, result, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    con.commit()
    con.close()

def get_recent_searches(limit=5):
    con = sqlite3.connect("travel_searches.db")
    cur = con.cursor()
    cur.execute("SELECT tool, query, city, timestamp FROM searches ORDER BY id DESC LIMIT ?", (limit,))
    data = cur.fetchall()
    con.close()
    return data

def clear_searches():
    con = sqlite3.connect("travel_searches.db")
    cur = con.cursor()
    cur.execute("DELETE FROM searches")
    con.commit()
    con.close()

init_db()

# function to get city name from the query
def extract_city(query):
    match = re.search(r"in ([A-Za-z\s]+)", query.lower())
    if match:
        return match.group(1).strip()
    return query.strip().split()[-1]

# function to get number of days from the query
def extract_days(query):
    match = re.search(r"(\d+)\s*day", query.lower())
    if match:
        return int(match.group(1))
    return 2

# travel plan tool
def travel_tool(query):
    city = extract_city(query)
    days = extract_days(query)

    prompt = f"""
You are a professional travel planner.
Create a realistic {days}-day travel plan for: {city.title()}

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
        return f"Error in travel tool: {str(e)}"

# weather tool
@st.cache_data
def weather_tool(query):
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Weather API key is missing"

    city = extract_city(query)

    try:
        url = f"http://api.weatherstack.com/current?access_key={api_key}&query={city}"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return "Weather service is not working right now"

        data = res.json()

        if "current" not in data or not data["current"]:
            return "City name is wrong or not found"

        temp = data["current"].get("temperature", "N/A")
        desc = data["current"].get("weather_descriptions", ["N/A"])[0]

        return f"Weather in {city.title()}: {temp}°C, {desc}"

    except requests.exceptions.Timeout:
        return "Weather API took too long to respond"
    except Exception as e:
        return f"Weather error: {str(e)}"

# hotel search tool
def hotel_tool(query):
    api_key = os.getenv("RAPIDAPI_KEY")
    city = extract_city(query)

    # first try the real booking API
    if api_key:
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }

        try:
            # step 1 - get the destination id
            dest_res = requests.get(
                "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination",
                headers=headers,
                params={"query": city},
                timeout=10
            )

            if dest_res.status_code == 429:
                raise Exception("quota finished")
            if dest_res.status_code != 200:
                raise Exception("api not working")

            dest_data = dest_res.json().get("data", [])
            if not dest_data:
                raise Exception("city not found")

            dest_id = dest_data[0].get("dest_id")
            dest_type = dest_data[0].get("search_type") or dest_data[0].get("dest_type") or "CITY"

            if not dest_id:
                raise Exception("no destination id")

            # step 2 - set checkin and checkout dates
            checkin = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
            checkout = (datetime.today() + timedelta(days=3)).strftime("%Y-%m-%d")

            # step 3 - search for hotels
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
                        raise Exception("quota finished")
                    break
                except requests.exceptions.Timeout:
                    if i == 2:
                        raise Exception("timeout")

            if hotel_res is None:
                raise Exception("no response from hotel api")

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

            # format the output
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
                output += f"   💰 Price  : ₹{int(float(price))}\n" if price else "   💰 Price  : N/A\n"
                output += "\n"

            if count == 0:
                raise Exception("could not get hotel details")

            return output

        except Exception:
            pass  # if api fails, use AI instead

    # if API fails use AI to suggest hotels
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
        return f"Hotel search error: {str(e)}"

# itinerary tool
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

# simple web search tool (demo)
def web_search_tool(query):
    return f"Search results for: {query}\n\n(This is a demo search tool)"

# function to decide which tool to use
def decide_tool(query):
    q = query.lower()
    if any(word in q for word in ["weather", "temperature", "climate"]):
        return "weather"
    elif any(word in q for word in ["hotel", "stay", "room", "accommodation"]):
        return "hotel"
    elif any(word in q for word in ["itinerary", "schedule", "day by day", "daywise"]):
        return "itinerary"
    elif any(word in q for word in ["trip", "plan", "travel", "visit"]):
        return "travel"
    elif any(word in q for word in ["news", "latest"]):
        return "search"
    else:
        return "chat"

# app title
st.title("🌍 AI Travel Assistant")

# sidebar for recent searches
with st.sidebar:
    st.header("Recent Searches")
    recent = get_recent_searches()
    if recent:
        for row in recent:
            tool, query, city, timestamp = row
            st.markdown(f"**{tool.upper()}** — {city or query}")
            st.caption(f"{timestamp}")
            st.divider()
    else:
        st.info("No searches yet.")
    if st.button("Clear History"):
        clear_searches()
        st.success("Cleared!")
        st.rerun()

# text input for user question
user_input = st.text_input("Ask your question:")

if user_input and not user_input.strip():
    st.warning("Please enter something!")
    st.stop()

# main logic
if user_input:
    try:
        tool = decide_tool(user_input)
        city = extract_city(user_input)

        if tool == "weather":
            result = weather_tool(user_input)
            st.success("🌦 Weather Tool Used")
            st.write(result)
            save_search("weather", user_input, city, result)

        elif tool == "hotel":
            result = hotel_tool(user_input)
            st.success("🏨 Hotel Tool Used")
            st.markdown(result)
            save_search("hotel", user_input, city, result)

        elif tool == "itinerary":
            days = extract_days(user_input)
            st.success(f"🗓️ Itinerary Tool Used")
            with st.spinner("Making your itinerary..."):
                result = itinerary_tool(user_input)
            st.markdown(result)
            save_search("itinerary", user_input, city, result)

        elif tool == "travel":
            result = travel_tool(user_input)
            st.success("🧳 Travel Tool Used")
            st.write(result)
            save_search("travel", user_input, city, result)

        elif tool == "search":
            result = web_search_tool(user_input)
            st.success("🌐 Search Tool Used")
            st.write(result)
            save_search("search", user_input, user_input, result)

        else:
            try:
                response = llm.invoke(user_input)
                result = response.content
            except Exception as e:
                result = f"AI error: {str(e)}"
            st.success("🤖 AI Response")
            st.write(result)
            save_search("chat", user_input, None, result)

    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")