<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { selectedBoundaryMap, selectedDistrict, selectedCoordinates, chatbotSelection } from '../stores';

  let userInput = '';
  let chatHistory: { sender: 'user' | 'bot'; text: string }[] = [];
  let loading = false;
  let minimized = false;

  // Gemini LLM chatbot (general, not entity-mapping)
  async function getGeminiResponse(query: string): Promise<{ response: string }> {
    try {
      const res = await fetch('/api/gemini-entity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, mode: 'chat' })
      });
      if (!res.ok) return { response: "Sorry, I couldn't get a response from Gemini." };
      const data = await res.json();
      return { response: data.response };
    } catch (e) {
      return { response: "Sorry, I couldn't get a response from Gemini." };
    }
  }

  async function handleSend() {
    if (!userInput.trim()) return;
    chatHistory = [...chatHistory, { sender: 'user', text: userInput }];
    loading = true;
    const botReply = await getGeminiResponse(userInput);
    loading = false;
    chatHistory = [
      ...chatHistory,
      {
        sender: 'bot',
        text: botReply.response
      }
    ];
    userInput = '';

    // --- Custom logic: parse division and area from bot reply ---
    // Example: "Division: bbmp_wards, Area: Koramangala"
    const match = botReply.response.match(/Division:\s*([\w_\- ]+)[,\n]+Area:\s*([\w\- ]+)/i);
    if (match) {
      const division = match[1].trim().toLowerCase().replace(/ /g, '_');
      const area = match[2].trim();
      // Remove lat/lng from URL and go to main page
      selectedCoordinates.set(null);
      await goto('/', { replaceState: true });
      // Set chatbot selection store
      chatbotSelection.set({ division, area });
    } else {
      // Always remove lat/lng from URL and go to main page
      selectedCoordinates.set(null);
      await goto('/', { replaceState: true });
      chatbotSelection.set({ division: null, area: null });
    }
  }
</script>

{#if browser}
  <div class="fixed bottom-6 right-6 z-50">
    {#if minimized}
      <button class="chatbot-minimize-btn-dark" aria-label="Open chatbot" on:click={() => minimized = false}>
        <svg width="28" height="28" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#23272f"/><path d="M8.5 10.5C8.5 9.11929 9.61929 8 11 8H13C14.3807 8 15.5 9.11929 15.5 10.5V13.5C15.5 14.8807 14.3807 16 13 16H11C9.61929 16 8.5 14.8807 8.5 13.5V10.5Z" stroke="#60a5fa" stroke-width="1.5"/><circle cx="10" cy="11" r="1" fill="#60a5fa"/><circle cx="14" cy="11" r="1" fill="#60a5fa"/></svg>
      </button>
    {:else}
      <div class="chatbot-container-dark animate-fade-in">
        <div class="chatbot-header-dark">
          <span class="font-semibold tracking-wide text-base">Bengaluru Civic Chatbot</span>
          <button class="chatbot-close-btn-dark" aria-label="Minimize chatbot" on:click={() => minimized = true}>
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24"><path stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M6 12h12"/></svg>
          </button>
        </div>
        <div class="chatbot-body-dark custom-scrollbar">
          {#each chatHistory as msg}
            <div class="chatbot-msg-row {msg.sender === 'user' ? 'justify-end' : 'justify-start'}">
              <span class="chatbot-msg-dark {msg.sender === 'user' ? 'chatbot-msg-user-dark' : 'chatbot-msg-bot-dark'}">{@html msg.text}</span>
            </div>
          {/each}
          {#if loading}
            <div class="chatbot-msg-row justify-start">
              <span class="chatbot-msg-dark chatbot-msg-bot-dark animate-pulse">Thinking...</span>
            </div>
          {/if}
        </div>
        <form class="chatbot-form-dark" on:submit|preventDefault={handleSend}>
          <input
            class="chatbot-input-dark"
            placeholder="Type your civic issue..."
            bind:value={userInput}
            autocomplete="off"
          />
          <button type="submit" class="chatbot-send-btn-dark">Send</button>
        </form>
      </div>
    {/if}
  </div>
{/if}

<style>
  .chatbot-container-dark {
    width: 370px;
    max-width: 100vw;
    background: #18181b;
    border-radius: 0.75rem;
    box-shadow: 0 8px 32px 0 rgba(0,0,0,0.55);
    border: 1px solid #23272f;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: fadeIn 0.5s;
  }
  .chatbot-header-dark {
    background: #23272f;
    color: #e0e7ef;
    padding: 0.9rem 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #23272f;
    font-size: 1rem;
    border-top-left-radius: 0.75rem;
    border-top-right-radius: 0.75rem;
    letter-spacing: 0.01em;
  }
  .chatbot-close-btn-dark {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 0.2rem 0.4rem;
    border-radius: 0.4rem;
    transition: background 0.2s;
  }
  .chatbot-close-btn-dark:hover {
    background: #1e293b;
  }
  .chatbot-body-dark {
    padding: 1.1rem 1.2rem;
    height: 320px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    background: transparent;
  }
  .chatbot-msg-row {
    display: flex;
  }
  .chatbot-msg-dark {
    max-width: 70%;
    padding: 0.7rem 1.05rem;
    border-radius: 0.7rem;
    font-size: 0.98rem;
    box-shadow: 0 1px 4px 0 rgba(31,41,55,0.10);
    word-break: break-word;
    line-height: 1.5;
  }
  .chatbot-msg-user-dark {
    background: #2563eb;
    color: #fff;
    border-bottom-right-radius: 0.2rem;
    border-bottom-left-radius: 0.7rem;
    border-top-right-radius: 0.7rem;
    border-top-left-radius: 0.7rem;
    align-self: flex-end;
    border: 1px solid #2563eb44;
    font-weight: 500;
    letter-spacing: 0.01em;
  }
  .chatbot-msg-bot-dark {
    background: #23272f;
    color: #e0e7ef;
    border-bottom-left-radius: 0.2rem;
    border-bottom-right-radius: 0.7rem;
    border-top-right-radius: 0.7rem;
    border-top-left-radius: 0.7rem;
    border: 1px solid #23272f;
    align-self: flex-start;
    font-weight: 400;
  }
  .chatbot-form-dark {
    display: flex;
    border-top: 1px solid #23272f;
    background: #18181b;
    padding: 0.7rem 1.2rem;
    border-bottom-left-radius: 0.75rem;
    border-bottom-right-radius: 0.75rem;
    gap: 0.4rem;
  }
  .chatbot-input-dark {
    flex: 1;
    padding: 0.65rem 1rem;
    border-radius: 0.5rem;
    border: 1px solid #23272f;
    font-size: 0.98rem;
    outline: none;
    background: #23272f;
    color: #e0e7ef;
    transition: border 0.2s, box-shadow 0.2s;
  }
  .chatbot-input-dark:focus {
    border: 1.5px solid #2563eb;
    box-shadow: 0 0 0 2px #2563eb44;
  }
  .chatbot-send-btn-dark {
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 0.5rem;
    padding: 0.65rem 1.2rem;
    font-weight: 600;
    font-size: 0.98rem;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s;
    box-shadow: 0 1px 4px 0 rgba(31,41,55,0.13);
  }
  .chatbot-send-btn-dark:hover {
    background: #1e40af;
  }
  .chatbot-minimize-btn-dark {
    width: 48px;
    height: 48px;
    background: #23272f;
    color: #60a5fa;
    border: none;
    border-radius: 50%;
    box-shadow: 0 2px 8px 0 rgba(31,41,55,0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s;
    z-index: 100;
    border: 1.5px solid #23272f;
  }
  .chatbot-minimize-btn-dark:hover {
    background: #18181b;
    box-shadow: 0 4px 16px 0 rgba(31,41,55,0.25);
  }
  .custom-scrollbar::-webkit-scrollbar {
    width: 8px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  @media (max-width: 500px) {
    .chatbot-container-dark {
      width: 100vw;
      right: 0;
      left: 0;
      bottom: 0;
      border-radius: 0;
      max-width: 100vw;
    }
    .fixed.bottom-6.right-6 {
      right: 0;
      left: 0;
      bottom: 0;
    }
  }
  .animate-fade-in {
    animation: fadeIn 0.5s;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
