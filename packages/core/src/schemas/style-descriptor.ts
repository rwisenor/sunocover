import { z } from 'zod';

export const styleVariantSchema = z.object({
  id: z.string().min(1, 'variant id is required'),
  label: z.string().min(1, 'variant label is required'),
  description: z.string().min(1).max(400, 'variant descriptions must be concise'),
});

export const styleDescriptorSchema = z.object({
  artist: z.string().min(1, 'artist is required'),
  preset: z.string().optional(),
  mood: z.array(z.string()).default([]),
  energy: z.enum(['low', 'medium', 'high']).default('medium'),
  vibe: z.string().optional(),
  notes: z.string().max(800).optional(),
  variants: z.array(styleVariantSchema).min(1),
  metadata: z
    .object({
      album: z.string().optional(),
      era: z.string().optional(),
      source: z.literal('suno-extension').default('suno-extension'),
    })
    .default({ source: 'suno-extension' }),
});

export type StyleDescriptor = z.infer<typeof styleDescriptorSchema>;
export type StyleVariant = z.infer<typeof styleVariantSchema>;

export const providerResponseSchema = z.object({
  descriptor: styleDescriptorSchema,
  warnings: z.array(z.string()).default([]),
  tokenUsage: z
    .object({
      prompt: z.number().nonnegative().optional(),
      completion: z.number().nonnegative().optional(),
    })
    .default({}),
});

export type ProviderResponse = z.infer<typeof providerResponseSchema>;
