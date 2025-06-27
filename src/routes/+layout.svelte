<script lang="ts">
  import '../app.css';
  import 'maplibre-gl/dist/maplibre-gl.css';
  import Analytics from '../components/Analytics.svelte';
  import SEO from '../components/SEO.svelte';
  import Chatbot from '../components/Chatbot.svelte'; // Add Chatbot import

  const hasAnalytics = Boolean(import.meta.env['VITE_GOOGLE_ANALYTICS_ID']);
</script>

{#if hasAnalytics}
  <Analytics />
{/if}
<SEO />
<slot />
<Chatbot /> <!-- Add Chatbot to all pages -->
