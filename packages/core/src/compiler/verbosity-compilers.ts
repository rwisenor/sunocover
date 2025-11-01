import type { StyleDescriptor } from '../schemas/style-descriptor';

export type VerbosityLevel = 'concise' | 'balanced' | 'detailed';

export interface CompilerOptions {
  readonly wordBudget: number;
}

export type DescriptorCompiler = (
  descriptor: StyleDescriptor,
  options?: Partial<CompilerOptions>
) => string;

const DEFAULT_BUDGETS: Record<VerbosityLevel, number> = {
  concise: 10,
  balanced: 40,
  detailed: 80,
};

const joinParts = (parts: string[]): string => parts.filter(Boolean).join(' ').trim();

const truncateToBudget = (input: string, budget: number): string => {
  const words = input.split(/\s+/);
  return words.slice(0, budget).join(' ');
};

const buildCompiler = (level: VerbosityLevel): DescriptorCompiler => {
  return (descriptor, options) => {
    const budget = options?.wordBudget ?? DEFAULT_BUDGETS[level];
    const baseParts = [descriptor.artist, descriptor.vibe ?? '', descriptor.notes ?? ''];
    const variant = descriptor.variants[0];
    const variantParts = [variant?.label ?? '', variant?.description ?? ''];
    const compiled = joinParts([...baseParts, ...variantParts]);
    return truncateToBudget(compiled, budget);
  };
};

export const conciseCompiler = buildCompiler('concise');
export const balancedCompiler = buildCompiler('balanced');
export const detailedCompiler = buildCompiler('detailed');

export const compilersByLevel: Record<VerbosityLevel, DescriptorCompiler> = {
  concise: conciseCompiler,
  balanced: balancedCompiler,
  detailed: detailedCompiler,
};
