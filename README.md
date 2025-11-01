# SunoCover Monorepo

This repository hosts both the legacy Python tooling for audio pre-processing and the
next-generation SunoCover browser extension. The project is structured as a multi-language
monorepo managed with `pnpm` workspaces for the web components while keeping Python utilities
isolated under `py/`.

## Project layout

```
.
├── data/                     # Structured datasets feeding the extension
├── packages/
│   ├── core/                 # Shared schemas, provider adapters, and compilers
│   ├── extension/            # Manifest V3 browser extension (Vite + TypeScript)
│   └── shared/               # Cross-package TypeScript types
├── py/                       # Original Python desktop application
└── README.md
```

## Getting started (JavaScript/TypeScript workspace)

1. Install [pnpm](https://pnpm.io/installation).
2. Install dependencies across the workspace:

   ```bash
   pnpm install
   ```

3. Run the extension in development mode:

   ```bash
   cd packages/extension
   pnpm dev
   ```

   The Vite dev server compiles the popup/options UIs and produces the extension bundle in
   `dist/` for use with Chrome or Chromium-based browsers. The content script currently ships
   with placeholder logic that will be replaced with artist tokenization and descriptor
   previews in upcoming milestones.

## Getting started (Python workspace)

The legacy audio processing utility lives under `py/`. Follow the instructions in
[`py/README.md`](py/README.md) to recreate the original desktop environment.

## Planned capabilities

The modernization track introduces:

- Schema-first descriptor generation with deterministic verbosity compilers (Concise ≤10
  words, Balanced ≤40 words, Detailed ≤80 words).
- Provider adapters for OpenAI, Anthropic, and Gemini with strict JSON guardrails.
- Manifest V3 extension with secure API key management, persona presets, and DOM previews on
  Suno's create page.
- IndexedDB-backed caching and persona datasets seeded with Rhett Wilder presets.
- Automated linting, testing (Vitest + Playwright), and release packaging via GitHub Actions.

Documentation in `docs/` will be expanded as the extension approaches MVP status.
