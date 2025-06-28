import { json } from '@sveltejs/kit';

export async function POST({ request }) {
  const { query } = await request.json();
  if (!query) return json({ error: 'No query provided' }, { status: 400 });

  // Call your local Python Ollama-based chatbot API
  try {
    const res = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    if (!res.ok) {
      return json({ error: 'Failed to get response from chatbot.' }, { status: 500 });
    }
    const data = await res.json();
    return json({ response: data.response });
  } catch (e) {
    return json({ error: 'Error connecting to chatbot backend.' }, { status: 500 });
  }
}
