import type { ProviderResponse } from '../schemas/style-descriptor';

export type ProviderName = 'openai' | 'anthropic' | 'gemini';

export interface ProviderAdapter {
  readonly name: ProviderName;
  readonly model: string;
  generateDescriptor(prompt: string): Promise<ProviderResponse>;
}

export interface ProviderRegistryOptions {
  readonly defaultProvider?: ProviderName;
}

export class ProviderRegistry {
  private readonly adapters = new Map<ProviderName, ProviderAdapter>();
  private readonly defaultProvider?: ProviderName;

  public constructor(options: ProviderRegistryOptions = {}) {
    this.defaultProvider = options.defaultProvider;
  }

  public register(adapter: ProviderAdapter): void {
    this.adapters.set(adapter.name, adapter);
  }

  public resolve(name?: ProviderName): ProviderAdapter {
    const key = name ?? this.defaultProvider;
    if (!key) {
      throw new Error('No provider specified and no default configured.');
    }

    const adapter = this.adapters.get(key);
    if (!adapter) {
      throw new Error(`Provider \"${key}\" has not been registered.`);
    }
    return adapter;
  }
}
