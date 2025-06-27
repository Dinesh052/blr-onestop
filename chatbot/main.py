import os
import chainlit as cl
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def ask_gemini(user_query: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    prompt = (
        f"You are an assistant for Bangalore city. "
        f"Answer the following user query using your own knowledge. "
        f"Reply with the relevant official's name, designation, department, area, phone, and email if available. "
        f"Be friendly and helpful. If you don't know, say so.\n\n"
        f"User query: \"{user_query}\""
    )
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "Sorry, I couldn't parse the response from Gemini."
    else:
        return f"Error: {response.status_code} - {response.text}"

@cl.on_chat_start
async def start():
    await cl.Message(
        content="Welcome to Bangalore City Gemini Chatbot!\n\n"
                "Ask your question about city officials or problems (e.g. 'Who do I call for water issues in Indiranagar?')."
    ).send()

@cl.on_message
async def main(message: cl.Message):
    user_query = message.content
    await cl.Message(content="Let me check...").send()
    answer = ask_gemini(user_query)
    await cl.Message(content=answer).send()