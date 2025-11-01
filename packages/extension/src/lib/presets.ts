import type { PersonaPreset } from '@sunocover/shared';

export const rhettWilderPresets: PersonaPreset[] = [
  {
    id: 'rhett-wilder-anthem',
    name: 'Rhett Wilder — Anthem',
    description: 'Arena-ready choruses with soaring vocals and euphoric synth swells.',
    tags: ['anthem', 'uplifting', 'stadium'],
  },
  {
    id: 'rhett-wilder-intimate',
    name: 'Rhett Wilder — Intimate',
    description: 'Acoustic storytelling with fragile falsetto and close-mic warmth.',
    tags: ['intimate', 'acoustic', 'singer-songwriter'],
  },
  {
    id: 'rhett-wilder-swagger',
    name: 'Rhett Wilder — Swagger',
    description: 'Slick funk grooves blended with neon pop hooks and confident delivery.',
    tags: ['swagger', 'funk', 'pop'],
  },
];

export const personaPresetIndex: Record<string, PersonaPreset> = rhettWilderPresets.reduce(
  (index, preset) => {
    index[preset.id] = preset;
    return index;
  },
  {} as Record<string, PersonaPreset>
);
