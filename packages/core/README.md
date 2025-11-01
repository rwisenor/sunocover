# @sunocover/core

Shared logic for the SunoCover extension lives in this package. It exposes Zod schemas for the
LLM response payload, deterministic verbosity compilers, and an adapter registry for AI
providers. The current implementation ships with placeholder compilers and registry plumbing so
extension development can begin before the provider adapters are wired to real APIs.
