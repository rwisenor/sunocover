import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

const App = () => {
  return (
    <main style={{ padding: '1rem', minWidth: 280 }}>
      <h1 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>SunoCover</h1>
      <p style={{ margin: 0 }}>
        Configure your provider, set verbosity presets, and inspect cached generations in
        future milestones.
      </p>
    </main>
  );
};

const container = document.getElementById('root');
if (!container) {
  throw new Error('Popup container missing.');
}

const root = createRoot(container);
root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
