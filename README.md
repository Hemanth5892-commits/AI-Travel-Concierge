# 🌍 AI Travel Assistant

An AI-powered travel chatbot built with Streamlit and LangChain that helps users plan trips, find hotels, check weather, generate itineraries, and search the web — all from a single chat interface.

---

## Features

- 🧳 **Travel Planner** — Day-by-day trip plans with activities, restaurants, and budget estimates
- 🏨 **Hotel Finder** — Real hotel results via Booking.com API with AI fallback
- 🌦 **Weather Checker** — Live weather data including temperature, humidity, and wind speed
- 🗓️ **Itinerary Generator** — Detailed schedules with packing tips and local notes
- 🌐 **Web Search** — Real-time DuckDuckGo search, no API key needed
- 💾 **Search History** — SQLite database stores all past searches
- 📥 **Export Chat** — Download full conversation as a `.txt` file

---

## Tech Stack

| Layer      | Technology                           |
|------------|--------------------------------------|
| Frontend   | Streamlit                            |
| Backend    | Python + LangChain                   |
| LLM        | Groq (Llama 3.1 8B Instant)          |
| Database   | SQLite                               |
| Search     | DuckDuckGo Search (duckduckgo-search)|
| Weather    | Weatherstack API                     |
| Hotels     | Booking.com via RapidAPI             |
| Deployment | Render                               |

---

## Project Structure

```
MY_travel/
├── app.py                  # Main application
├── requirements.txt        # Python dependencies
├── .env                    # API keys (never commit this)
├── .gitignore              # Excludes .env and other files
└── README.md               # This file
```

> `travel_searches.db` is auto-created at runtime. On Render it is stored in `/tmp/`, locally it is created in the project folder.

---

## Setup Instructions (Local)

### 1. Clone the repository

```bash
git clone https://github.com/Hemanth5892-commits/AI-Travel-Concierge.git
cd AI-Travel-Concierge
```

### 2. Create a virtual environment

```bash
python -m venv cleanenv
# Windows
cleanenv\Scripts\activate
# Mac/Linux
source cleanenv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

Create a file named `.env` in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
WEATHER_API_KEY=your_weatherstack_api_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

> **Note:** `WEATHER_API_KEY` and `RAPIDAPI_KEY` are optional. The app works without them using AI fallbacks. Only `GROQ_API_KEY` is required.

### 5. Run the app

```bash
python -m streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Deployment (Render)

This project is deployed on [Render](https://render.com).

### Steps to deploy

1. Push your code to GitHub (make sure `.env` is in `.gitignore`)
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub account and select this repository
4. Fill in the following settings:

| Field | Value |
|-------|-------|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |

5. Go to the **Environment** tab and add your API keys:

```
GROQ_API_KEY      = your_key_here
WEATHER_API_KEY   = your_key_here
RAPIDAPI_KEY      = your_key_here
```

6. Click **Deploy** ✅

> Every time you push to GitHub, Render will automatically redeploy the app.

---

## API Keys — Where to Get Them

| Key | Where to get | Free tier |
|-----|-------------|-----------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Yes |
| `WEATHER_API_KEY` | [weatherstack.com](https://weatherstack.com) | Yes (1000 calls/month) |
| `RAPIDAPI_KEY` | [rapidapi.com](https://rapidapi.com) → Booking.com API | Yes (limited) |

---

## How to Use

Type any of these in the chat box:

| What you want | Example query |
|---------------|--------------|
| Travel plan   | `3 day trip to Goa` |
| Hotels        | `hotels in Hyderabad` |
| Weather       | `weather in Delhi` |
| Itinerary     | `5 day itinerary in Manali` |
| Web search    | `search what is Charminar` |
| General chat  | `what currency is used in Japan` |

---

## Important Notes

- Never commit your `.env` file — it contains secret API keys
- The `.gitignore` must include `.env` to avoid accidental exposure
- If Booking.com API quota is exceeded, the app automatically falls back to AI-generated hotel suggestions
- DuckDuckGo search may occasionally rate-limit — wait a moment and retry
- On Render, the SQLite database resets on every redeploy (stored in `/tmp/`)

---

## Architecture

```
User Input
    ↓
decide_tool()  ←— keyword-based router
    ↓
┌─────────────────────────────────────┐
│  weather_tool  → Weatherstack API   │
│  hotel_tool    → Booking API / LLM  │
│  travel_tool   → Groq LLM           │
│  itinerary_tool→ Groq LLM           │
│  web_search    → DuckDuckGo         │
│  chat          → Groq LLM           │
└─────────────────────────────────────┘
    ↓
save_search() → SQLite DB
    ↓
Display in Streamlit chat UI
```

---

## Team

Built as part of the AI Travel Concierge project — Track A (Essential Track)  
Capabl. — 8 Week AI Agent Development Program