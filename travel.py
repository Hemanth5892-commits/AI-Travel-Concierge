import streamlit as st
from langchain_groq import ChatGroq
import os

# Initialize LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7,
    max_tokens=1024,
)

# -------- TOOL FUNCTIONS --------

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


# -------- UI --------

st.title("AI Travel Assistant (Agent Mode)")

user_input = st.text_input("Ask your travel question:")

# -------- AGENT LOGIC --------

if user_input:
    try:
        # Step 1: Decision making
        decision_prompt = f"""
You are an AI agent.

User Query: {user_input}

Decide:
- If it needs real-time info or factual lookup → respond ONLY "SEARCH"
- If general advice → respond ONLY "CHAT"
"""

        decision = llm.invoke(decision_prompt).content.strip().upper()

        # Step 2: Tool or LLM
        if "SEARCH" in decision:
            result = travel_tool(user_input)
            st.success("🔎 Tool Used")
            st.write(result)

        else:
            response = llm.invoke(user_input)
            st.success("🤖 AI Response")
            st.write(response.content)

    except Exception as e:
        st.error(f"Error: {e}")