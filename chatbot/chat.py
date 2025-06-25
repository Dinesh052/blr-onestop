import pandas as pd
import json
import asyncio
from typing import List, Dict, Any, Optional
import ollama
import chainlit as cl
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BangaloreCityBot:
    """Chatbot that uses Excel sheet as knowledge base with Ollama"""

    def __init__(self, excel_path: str, model_name: str = "qwen2.5:7b"):
        self.excel_path = excel_path
        self.model_name = model_name
        self.client = ollama.Client()
        self.df = None
        self.contacts_data = []

    async def initialize(self):
        await self.load_database()
        return True  # Skip model check for now

    async def load_database(self):
        try:
            self.df = pd.read_excel(self.excel_path)
            self.df = self.df.fillna("")
            self.contacts_data = []
            for _, row in self.df.iterrows():
                if any([str(row['Department']), str(row['Area']), str(row['Name'])]):
                    contact = {
                        'Department': str(row['Department']),
                        'Area': str(row['Area']),
                        'Designation': str(row['Designation']),
                        'Name': str(row['Name']),
                        'Phone': str(row['Phone']),
                        'Email': str(row['E-Mail']),
                        'Notes': str(row.get('Notes', ''))
                    }
                    self.contacts_data.append(contact)
            logger.info(f"Loaded database with {len(self.df)} records, {len(self.contacts_data)} valid contacts")
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            raise Exception(f"Could not load Excel file: {e}")

    async def get_response(self, query: str) -> str:
        prompt = f"""You are an AI assistant helping citizens of Bangalore find the right government officials for their problems.

USER QUERY: "{query}"

CONTACT DATABASE:
{json.dumps(self.contacts_data[:50], indent=1)}  # Limit to first 50 for context window

INSTRUCTIONS:
1. Analyze the user's query to understand their issue and location (if mentioned)
2. Find the most relevant contacts from the database
3. If you find specific area/location contacts, prioritize those
4. If no specific location contacts found, provide district/general contacts for that department
5. Provide a helpful response with contact details

RESPONSE FORMAT:
- Start with understanding their issue
- Provide relevant contact information clearly formatted
- Include name, designation, department, area, phone, email if available
- Give actionable advice on what to do next
- Be conversational and helpful
- Use emojis to make it more friendly

Please provide your response now:"""

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={
                        'temperature': 0.3,
                        'max_tokens': 800,
                        'top_p': 0.9
                    }
                )
            )
            return response['response'].strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._create_fallback_response(query)

    def _create_fallback_response(self, query: str) -> str:
        return f"""🤖 I understand you're asking about: "{query}"

I'm having trouble processing your request right now, but here are some general contacts that might help:

📋 **General Contacts:**
- 🏛️ **BBMP** - For municipal issues
- ⚡ **BESCOM** - For electricity issues  
- 💧 **BWSSB** - For water/sewage issues
- 🚔 **Police** - For safety/security matters

Please try rephrasing your query or contact the general municipal helpline for immediate assistance. 📞"""

bot = None

@cl.on_chat_start
async def start():
    global bot
    loading_msg = cl.Message(content="🚀 Initializing Bangalore City Officials Chatbot...")
    await loading_msg.send()

    try:
        excel_path = "sheet.xlsx"
        if not Path(excel_path).exists():
            loading_msg.content = f"❌ **Excel file not found:** {excel_path}\n\nPlease make sure 'sheet.xlsx' is in the same directory as the application."
            await loading_msg.update()
            return

        loading_msg.content = "📊 Loading city officials database..."
        await loading_msg.update()

        bot = BangaloreCityBot(excel_path)
        await bot.load_database()

        loading_msg.content = f"✅ Database loaded: {len(bot.contacts_data)} contacts found\n\n🤖 Ready to serve your queries using `qwen2.5:7b` model."
        await loading_msg.update()

        welcome_msg = cl.Message(content="""# 🏛️ Welcome to Bangalore City Officials Chatbot!

I'm here to help you find the right government contacts for your issues in Bangalore.

## 🎯 How to use me:
- Describe your problem or service need
- Mention your area/locality if relevant
- I'll find the right officials and their contact information

## 💬 Example queries:
- "No electricity in Yelahanka"
- "Water problem in Indiranagar" 
- "Traffic police contact for Rajajinagar"
- "Garbage collection issue"
- "Property tax office contact"

**Just type your query below and I'll help you! 👇**""")
        await welcome_msg.send()

        cl.user_session.set("bot", bot)

    except Exception as e:
        loading_msg.content = f"❌ Initialization Error:\n\n{str(e)}"
        await loading_msg.update()

@cl.on_message
async def main(message: cl.Message):
    global bot
    bot = cl.user_session.get("bot")

    if not bot:
        await cl.Message(content="❌ Bot not initialized. Please refresh the page.").send()
        return

    async with cl.Step(name="Searching contacts", type="run") as step:
        step.output = "🔍 Analyzing your query and searching for relevant contacts..."

        try:
            response = await bot.get_response(message.content)
            step.output = "✅ Found relevant contacts!"
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            response = "❌ I encountered an error while processing your request. Please try again."
            step.output = "❌ Error occurred during search"

    await cl.Message(content=response).send()

@cl.on_chat_end
async def end():
    logger.info("Chat session ended")

@cl.cache
def get_bot_config():
    return {
        "name": "Bangalore City Officials Bot",
        "description": "Find the right government contacts for your city issues"
    }

if __name__ == "__main__":
    print("Please run with: chainlit run app.py")
