# SunoCover Modernization Scaffold

This document captures the initial scaffolding decisions for the browser extension initiative.
It will evolve into full engineering documentation as implementation proceeds.

## Workspace overview

- `pnpm` manages the JavaScript/TypeScript packages in `packages/`.
- Shared compiler logic and provider abstractions live in `packages/core`.
- Extension-specific UI, manifest configuration, and content scripts are colocated in
  `packages/extension` and bundled with Vite.
- Cross-cutting types and utilities belong in `packages/shared`.
- Legacy Python automation remains in `py/` to avoid introducing Node dependencies into
  existing workflows.

## Next steps

1. Flesh out provider adapters with real HTTP clients and streaming/guardrail handling.
2. Implement tokenizer-aware word budgeting in the compilers.
3. Wire the content script to the Suno UI for artist tokenization, fuzzy matching, and preview
   tooltips before DOM mutation.
4. Integrate secure WebCrypto-backed storage for API keys in the options UI.
5. Configure Vitest unit tests and Playwright integration suites.
6. Publish CI workflows and prepare signed extension builds for release.
