import { balancedCompiler } from '@sunocover/core';
import type { StyleDescriptor } from '@sunocover/core';

declare global {
  interface Window {
    __sunocoverContentBootstrapped?: boolean;
  }
}

const bootstrap = () => {
  if (window.__sunocoverContentBootstrapped) {
    return;
  }
  window.__sunocoverContentBootstrapped = true;
  console.warn('[SunoCover] Content script initialized.');

  const target = document.querySelector('textarea');
  if (!target) {
    return;
  }

  target.addEventListener('focus', () => {
    const descriptor: StyleDescriptor = {
      artist: 'Placeholder Artist',
      energy: 'medium',
      mood: ['uplifting'],
      variants: [
        {
          id: 'balanced',
          label: 'Balanced Demo',
          description: 'Warm guitars with crisp percussion and cinematic lift.',
        },
      ],
      metadata: {
        source: 'suno-extension',
      },
    };

    const compiled = balancedCompiler(descriptor);
    target.setAttribute('data-sunocover-preview', compiled);
  });
};

document.addEventListener('readystatechange', () => {
  if (document.readyState === 'complete') {
    bootstrap();
  }
});

bootstrap();
