# SunoCover Modernization Plan

This repository currently ships a Python-based desktop utility for processing audio before uploading to Suno. The next phase of work introduces a schema-driven browser extension that generates structured "Styles" descriptors directly on the client and replaces the existing macro-based approach described in prior discussions.

## Scope confirmation

* **Target repositories:** Focus on `rwisenor/sunocover`. If no artist-style fork exists under the account, bootstrap the extension inside this repository rather than creating an additional GitHub project. The browser extension and shared logic can live inside a new `packages/` workspace while the current Python utilities remain in their own top-level directory (e.g., `/py`), preventing dependency entanglement.
* **Default verbosity:** Use the **Balanced (≤40 tokens)** compiler output as the initial setting in the user interface. Concise and Detailed modes remain available as alternatives.

## High-level roadmap

1. **Workspace scaffolding**
   * Introduce a `pnpm`-managed workspace with `packages/core` and `packages/extension` subprojects while retaining the current Python tooling in an isolated directory.
   * Add shared configuration for TypeScript, ESLint (strict), and Prettier.
   * Define baseline `tsconfig`, lint, and prettier rules that can be shared across packages without impacting Python development environments.

2. **Core package**
   * Define Zod schemas for the LLM JSON response and the compiled string variants.
   * Implement a narrow provider adapter interface (OpenAI, Anthropic, Gemini) so provider-specific JSON quirks remain contained and never leak into extension UI logic. Prompts run at temperature `0.2` with guardrails that force JSON-only output.
   * Build the Concise, Balanced, and Detailed compilers that convert structured descriptors into word-budgeted strings (≤10, ≤40, ≤80 words respectively) for Suno, keeping implementations deterministic until tokenizer-based budgets ship later.

3. **Extension package**
   * Scaffold a Manifest V3 extension via Vite + TypeScript with `src/content`, `src/background`, `src/popup`, and `src/options` directories.
   * Implement artist tokenization and fuzzy matching within the content script. Surface preview tooltips before replacing any text on Suno's create page.
   * Provide a popup/options UI to manage encrypted API keys, choose providers, toggle local-only mode, inspect cache entries, and select verbosity presets.
   * Configure Manifest host permissions and `content_security_policy` so only the supported vendor API origins are allowed while maintaining the tightest feasible CSP for extension pages.

4. **Persona presets and heuristics**
   * Seed presets for "Rhett Wilder" (Anthem, Intimate, Swagger) and store them in IndexedDB.
   * Detect optional era and album context (e.g., `Artist – Album (2007)`) and pass the normalized metadata into the generation pipeline.

5. **Privacy and security**
   * Store vendor API keys encrypted with WebCrypto (PBKDF2 + AES-GCM) and never proxy through third-party servers.
   * Default to session-only storage for API keys; allow opt-in encryption-at-rest behind a "Remember my keys" toggle.
   * Add a one-click action that wipes keys and cached generations, and clearly log which vendor hostname receives each request (without exposing key material).

6. **Testing and automation**
   * Cover schema validation and compiler behavior with Vitest.
   * Use Playwright to assert DOM replacement flows against a mocked Suno page, avoiding traffic to production Suno endpoints during CI runs.
   * Configure GitHub Actions to run linting, type checks, unit tests, and Playwright suites on every pull request.

7. **Documentation and release**
   * Update the main `README.md` with architecture diagrams, security notes, and usage instructions for the extension.
   * Add `SECURITY.md` to capture the threat model and key-handling guarantees.
   * Produce a demo GIF and attach a signed extension package to a draft GitHub release when features reach MVP quality.

This plan preserves the existing Python application while adding the modernized, privacy-conscious browser extension and supporting infrastructure requested in the latest requirements.
