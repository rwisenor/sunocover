export interface CachedGenerationMetadata {
  readonly id: string;
  readonly artist: string;
  readonly createdAt: string;
  readonly provider: 'openai' | 'anthropic' | 'gemini';
  readonly verbosity: 'concise' | 'balanced' | 'detailed';
}

export interface PersonaPreset {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly tags: string[];
}
