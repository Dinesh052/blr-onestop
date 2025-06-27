import { json } from '@sveltejs/kit';

const GEMINI_API_KEY = 'AIzaSyC5U-h0i4xsDdKAmuq-GeRSqrWGlZLVsAk';

const entityMap = {
  bbmp: 'bbmp_wards',
  bescom: 'bescom_division',
  bwssb: 'bwssb_division',
  police: 'police_city',
  traffic: 'police_traffic',
  registration: 'stamps_sro',
  registrar: 'stamps_dro',
  pincode: 'pincode',
  zone: 'bbmp_zone',
  ward: 'bbmp_wards',
  subdivision: 'bescom_subdivision',
  service: 'bwssb_service_station',
  district: 'admin_district',
  taluk: 'admin_taluk',
  election: 'election_ac',
  parliament: 'election_pc',
  tree: 'bbmp_wards',
  wire: 'bescom_division',
  cable: 'bescom_division',
  electric: 'bescom_division',
  power: 'bescom_division',
  branch: 'bbmp_wards',
  fallen: 'bbmp_wards',
  hanging: 'bescom_division',
  tangle: 'bescom_division',
  entangle: 'bescom_division',
  dangerous: 'bescom_division',
  hazard: 'bescom_division'
};

export async function POST({ request }) {
  const { query, mode } = await request.json();
  if (!query) return json({ error: 'No query provided' }, { status: 400 });

  if (mode === 'chat') {
    // Gemini chatbot mode: return division in ALL CAPS and area name, then detailed website steps
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`;
    const headers = { 'Content-Type': 'application/json' };
    const prompt = `Given the following user query about Bengaluru civic issues, reply in two parts:\n\n1. On the first line, reply ONLY with the most relevant government entity/division (from this list: BBMP, BESCOM, BWSSB, POLICE, TRAFFIC, REGISTRATION, REGISTRAR, PINCODE, ZONE, WARD, SUBDIVISION, SERVICE, DISTRICT, TALUK, ELECTION, PARLIAMENT) in ALL CAPS, followed by a colon and the most relevant area name (e.g., BESCOM: Indiranagar). If nothing matches, reply with 'NONE: none'.\n\n2. On the next lines, provide clear, step-by-step instructions for how a user can access this division and area using the website interface. The instructions should be specific to the following UI flow:\n- Use the main search bar at the top to search for the area name.\n- After searching, the sidebar on the right will show the relevant divisions.\n- Click on the division name in the sidebar to view more details.\n- You can also use the search bar within the sidebar to further filter or find the area.\n- The sidebar will display details for the selected division and area.\nMake sure the instructions match this navigation and UI flow.\n\nUser query: \"${query}\"`;
    const data = {
      contents: [
        {
          parts: [
            { text: prompt }
          ]
        }
      ]
    };
    const geminiRes = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    });
    if (geminiRes.ok) {
      const result = await geminiRes.json();
      try {
        const response = result.candidates[0].content.parts[0].text.trim();
        // Expecting format: DIVISION: AreaName
        const [division, area] = response.split(':').map(s => s.trim());
        return json({ division, area, response });
      } catch (e) {
        return json({ response: "Sorry, I couldn't parse the response from Gemini." });
      }
    } else {
      const err = await geminiRes.text();
      return json({ response: `Error: ${geminiRes.status} - ${err}` });
    }
  }

  // Entity-mapping mode
  const geminiRes2 = await fetch(
    'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=AIzaSyC5U-h0i4xsDdKAmuq-GeRSqrWGlZLVsAk',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              {
                text: `Given the following user query about Bengaluru civic issues, choose the most relevant government entity key from this list: [${Object.values(entityMap).join(', ')}]. The keywords for each entity are: ${Object.entries(entityMap).map(([k,v])=>`${k}: ${v}`).join(', ')}. If the query involves both trees and wires, prefer 'bescom_division'. Reply with just the key, no explanation, no extra text, no punctuation. If nothing matches, reply with 'none'. Query: "${query}"`
              }
            ]
          }
        ]
      })
    }
  );

  const geminiData2 = await geminiRes2.json();
  let entityKey = null;
  if (geminiData2 && geminiData2.candidates && geminiData2.candidates[0]) {
    const text = geminiData2.candidates[0].content.parts[0].text.trim();
    if (Object.values(entityMap).includes(text)) {
      entityKey = text;
    } else if (text.toLowerCase() === 'none') {
      entityKey = null;
    }
  }

  return json({ entityKey });
}
