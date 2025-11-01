import { StrictMode, useState } from 'react';
import { createRoot } from 'react-dom/client';

type Provider = 'openai' | 'anthropic' | 'gemini';

const App = () => {
  const [provider, setProvider] = useState<Provider>('openai');
  return (
    <main style={{ padding: '1.5rem', maxWidth: 520 }}>
      <h1 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>SunoCover Options</h1>
      <label style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <span>Default Provider</span>
        <select value={provider} onChange={(event) => setProvider(event.target.value as Provider)}>
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="gemini">Google Gemini</option>
        </select>
      </label>
      <p style={{ marginTop: '1rem' }}>
        API key storage, encryption, and cache visibility will be wired in upcoming iterations.
      </p>
    </main>
  );
};

const container = document.getElementById('root');
if (!container) {
  throw new Error('Options container missing.');
}

const root = createRoot(container);
root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
