# 🌍 AI Travel Assistant

An AI-powered travel planning chatbot built with Streamlit and LangChain. It helps users plan trips, find hotels, check weather, and generate day-by-day itineraries using real-world APIs and an LLM backend.

---

## 🚀 Features

| Tool | Trigger Keywords | Description |
|------|-----------------|-------------|
| 🧳 Travel Planner | trip, plan, travel, visit | Multi-day travel plan with budget estimate |
| 🏨 Hotel Finder | hotel, stay, room, accommodation | Real hotel search via Booking API (falls back to AI) |
| 🌦 Weather | weather, temperature, climate | Live weather via Weatherstack API |
| 🗓️ Itinerary | itinerary, schedule, day by day | Detailed day-wise itinerary with packing tips |
| 🤖 General Chat | anything else | General travel Q&A via LLM |

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python + LangChain
- **LLM:** Groq (Llama 3.1 8B)
- **Database:** SQLite (search history)
- **APIs:** Weatherstack, Booking.com (via RapidAPI)

---

## 📁 Project Structure

```
MY_travel/
│
├── app.py                  # Main Streamlit application
├── .env                    # API keys (never commit this!)
├── .gitignore              # Includes .env
├── requirements.txt        # Python dependencies
├── travel_searches.db      # SQLite DB (auto-created on first run)
└── README.md               # This file
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get API Keys

You need the following API keys:

| Key | Where to Get It | Required? |
|-----|----------------|-----------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | ✅ Yes |
| `WEATHER_API_KEY` | [weatherstack.com](https://weatherstack.com) | ⚠️ Optional |
| `RAPIDAPI_KEY` | [rapidapi.com](https://rapidapi.com) → Booking.com API | ⚠️ Optional |

> If `WEATHER_API_KEY` or `RAPIDAPI_KEY` are missing, those tools will fall back to AI-generated responses automatically.

### 5. Create the `.env` File

Create a file named `.env` in the project root:

```
GROQ_API_KEY=your_groq_key_here
WEATHER_API_KEY=your_weatherstack_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

> ⚠️ **Never commit your `.env` file to GitHub!** Make sure `.env` is listed in `.gitignore`.

### 6. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

---

## 📦 Requirements

Create a `requirements.txt` file with the following:

```
streamlit
langchain
langchain-groq
python-dotenv
requests
```

Install them with:

```bash
pip install -r requirements.txt
```

---

## 💬 Example Queries

```
Show hotels in Goa
3 day itinerary in Manali
Weather in Delhi
Plan a 5 day trip to Rajasthan
Day by day schedule for Ooty
```

---

## 🗄️ Database

Search history is saved automatically to `travel_searches.db` (SQLite).  
You can clear it anytime using the **🗑️ Clear History** button in the sidebar.

---

## ☁️ Deployment (Streamlit Cloud)

1. Push your code to a **public GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New App** → select your repo and `app.py`
4. Go to **Advanced Settings → Secrets** and add your keys:

```
GROQ_API_KEY = "your_groq_key_here"
WEATHER_API_KEY = "your_weatherstack_key_here"
RAPIDAPI_KEY = "your_rapidapi_key_here"
```

5. Click **Deploy** ✅

> Do **not** upload your `.env` file to GitHub. Use Streamlit Cloud's Secrets section instead.

---

## 🔒 Security Notes

- Store all API keys in `.env` locally and in Streamlit Secrets when deployed
- `.env` is listed in `.gitignore` — never remove it from there
- If a key is accidentally pushed to GitHub, **revoke it immediately** and generate a new one

---

## 👥 Team

| Name | Role |
|------|------|
| Member 1 | Backend / API Integration |
| Member 2 | Frontend / UI |
| Member 3 | LLM Prompting / Testing |
| Member 4 | Deployment / Documentation |

---

## 🙏 Acknowledgements

- [Groq](https://groq.com) for the free LLM API
- [Weatherstack](https://weatherstack.com) for weather data
- [Booking.com via RapidAPI](https://rapidapi.com) for hotel search
- [Streamlit](https://streamlit.io) for the UI framework
- [LangChain](https://langchain.com) for LLM tooling
