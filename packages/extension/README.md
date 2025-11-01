# @sunocover/extension

Manifest V3 browser extension that integrates SunoCover's schema-driven style generation into
Suno's web experience.

## Directories

- `public/` — Static assets shipped with the extension, including the manifest and icons.
- `src/background/` — Service worker orchestrating provider requests and cache management.
- `src/content/` — Content scripts injected into Suno's create page.
- `src/popup/` — User-facing controls exposed in the toolbar popup.
- `src/options/` — Advanced configuration UI for API keys, storage, and debugging tools.
- `src/lib/` — Shared utilities, dataset loaders, and persona preset exports.

## Development

```bash
pnpm install
pnpm --filter @sunocover/extension dev
```

Load the resulting `dist/` directory as an unpacked extension in Chrome to preview the popup,
options, and content script wiring.
