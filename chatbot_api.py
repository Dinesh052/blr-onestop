from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import uvicorn
import pandas as pd
from pathlib import Path
from difflib import SequenceMatcher
import json
import ollama
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Department keywords mapping
DEPARTMENT_KEYWORDS = {
    "electricity": "BESCOM",
    "power": "BESCOM",
    "no power": "BESCOM",
    "load shedding": "BESCOM",
    "blackout": "BESCOM",
    "voltage": "BESCOM",
    "water": "BWSSB",
    "sewage": "BWSSB",
    "drainage": "BWSSB",
    "garbage": "BBMP",
    "trash": "BBMP",
    "waste": "BBMP",
    "sanitation": "BBMP",
    "streetlight": "BBMP",
    "pothole": "BBMP",
    "road": "BBMP",
    "property tax": "BBMP",
    "police": "Police",
    "theft": "Police",
    "crime": "Police",
    "traffic": "Traffic Police",
    "accident": "Traffic Police",
}

def infer_department_from_query(query: str) -> str:
    query = query.lower()
    for keyword, dept in DEPARTMENT_KEYWORDS.items():
        if keyword in query:
            return dept
    return ""

class BangaloreCityBot:
    def __init__(self, excel_path: str, model_name: str = "llama3:8b"):
        self.excel_path = excel_path
        self.model_name = model_name
        self.client = ollama.Client()
        self.df = None
        self.contacts_data = []

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

    def is_relevant(self, contact, query: str) -> bool:
        query = query.lower()
        return any(
            query in str(value).lower() or
            SequenceMatcher(None, query, str(value).lower()).ratio() > 0.75
            for value in contact.values()
        )

    async def get_response(self, query: str) -> str:
        filtered_contacts = [c for c in self.contacts_data if self.is_relevant(c, query)]
        filtered_contacts = filtered_contacts[:15]
        if not filtered_contacts:
            inferred_dept = infer_department_from_query(query)
            if inferred_dept:
                filtered_contacts = [
                    c for c in self.contacts_data
                    if inferred_dept.lower() in c["Department"].lower()
                ][:5]
            else:
                filtered_contacts = [
                    c for c in self.contacts_data
                    if "bbmp" in c["Department"].lower()
                ][:5]
        prompt = f"""You are an AI assistant helping citizens of Bangalore find the right government officials for their problems.\n\nUSER QUERY: \"{query}\"\n\nCONTACT DATABASE:\n{json.dumps(filtered_contacts, indent=1)}\n\nINSTRUCTIONS:\n1. Analyze the user's query to understand their issue and location (if mentioned)\n2. Find the most relevant contacts from the database\n3. If you find specific area/location contacts, prioritize those\n4. If no specific location contacts found, provide district/general contacts for that department\n5. Provide a helpful response with contact details\n\nRESPONSE FORMAT:\n- Start with understanding their issue\n- Provide relevant contact information clearly formatted\n- Include name, designation, department, area, phone, email if available\n- Give actionable advice on what to do next\n- Be conversational and helpful and friendly\n- Use emojis to make it more friendly\n\nPlease provide your response now:"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={
                        'temperature': 0.3,
                        'max_tokens': 80000,
                        'top_p': 0.9
                    }
                )
            )
            return response['response'].strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._create_fallback_response(query)

    def _create_fallback_response(self, query: str) -> str:
        return f"""🤖 I understand you're asking about: \"{query}\"\n\nI'm having trouble processing your request right now, but here are some general contacts that might help:\n\n📋 *General Contacts:*\n- 🏛 *BBMP* - For municipal issues\n- ⚡ *BESCOM* - For electricity issues  \n- 💧 *BWSSB* - For water/sewage issues\n- 🚔 *Police* - For safety/security matters\n\nPlease try rephrasing your query or contact the general municipal helpline for immediate assistance. 📞"""

# FastAPI setup
app = FastAPI()
bot = None

class QueryRequest(BaseModel):
    query: str

@app.on_event("startup")
async def startup_event():
    global bot
    excel_path = r"C:\\Users\\91944\\BLR_STOP\\blr-onestop\\sheet.xlsx"  # <-- Change this path to your Excel file
    if not Path(excel_path).exists():
        logger.error(f"Excel file not found: {excel_path}")
        raise Exception(f"Excel file not found: {excel_path}")
    bot = BangaloreCityBot(excel_path)
    await bot.load_database()

@app.post("/chat")
async def chat_endpoint(req: QueryRequest):
    global bot
    response = await bot.get_response(req.query)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run("chatbot_api:app", host="127.0.0.1", port=8000, reload=True)
