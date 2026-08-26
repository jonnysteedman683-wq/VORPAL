---
name: model-marketplace-research
description: "Research model providers and free tiers for task fit."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [models, providers, pricing, free-tier, openrouter, ollama, huggingface, research]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [hermes-agent]
---

# Model Marketplace Research

Research and compare LLM providers, pricing tiers, and model capabilities to find the best fit for a task or budget. Covers cloud providers (OpenRouter, Anthropic, OpenAI, Google, etc.), local inference (Ollama, LM Studio), and free tiers.

## When to Use

- User asks "what free models are available?" or "list models on [provider]"
- Comparing providers for cost/performance tradeoffs
- Finding models with specific capabilities (long context, tool calling, reasoning)
- Evaluating whether to use cloud vs local inference
- Building model aliases for Hermes config

## Core Workflows

### 1. Browse OpenRouter Free Models

**Quick filter method:**
1. Navigate to `https://openrouter.ai/models`
2. Open "Prompt pricing" filter sidebar
3. Drag maximum slider to **$0** (or minimum to "FREE" marker)
4. Switch to "Table view" for sortable columns
5. Sort by "Weekly Tokens" for popularity/reliability signal

**Current free models (Aug 2026):**
| Model | Provider | Context | Weekly Tokens | Best For |
|-------|----------|---------|---------------|----------|
| **NVIDIA: Nemotron 3 Ultra (free)** | NVIDIA | 1M tokens | 2.7T | Agent orchestration, multi-step reasoning, coding agents, deep research |
| **Ling-3.0-flash (free)** | InclusionAI | 262K tokens | 1.49T | Fast agentic tasks, token efficiency, production-scale inference |
| **Poolside: Laguna S 2.1 (free)** | Poolside | 262K tokens | 859B | Programming-specialized (#45 rank in Programming) |
| **Poolside: Laguna XS 2.1 (free)** | Poolside | 262K tokens | 194B | Lightweight programming variant |
| **Fish Audio: S2.1 Pro Free (free)** | Fish Audio | — | 831K | Speech-to-text / TTS |
| **NVIDIA: Nemotron 3 Nano 30B A3B (free)** | NVIDIA | 256K tokens | 49.2B | Efficient reasoning, lower latency alternative |
| **NVIDIA: Nemotron 3 Nano Omni (free)** | NVIDIA | 256K tokens | 36.1B | Multimodal capable nano model |
| **Google: Gemma 4 26B A4B (free)** | Google | 262K tokens | 16.5B | Open-weight alternative with strong performance |
| **NVIDIA: Nemotron Nano 9B V2 (free)** | NVIDIA | 128K tokens | 16.2B | Compact, fast inference |
| **NVIDIA: Nemotron Nano 12B 2 VL (free)** | NVIDIA | 128K tokens | 11.5B | Vision-language capable nano model |

> **Note:** OpenRouter "free" models are sponsored/partner models — providers cover inference costs. Rate limits apply; availability may change. Weekly token volume indicates community usage and reliability signal.

### 2. Local Free Models (Ollama)

**Truly unlimited free inference** — run on your hardware:

```bash
# Install Ollama
winget install Ollama.Ollama  # Windows
# or: curl -fsSL https://ollama.com/install.sh | sh  # Linux/macOS

# Pull models (all free, no API keys)
ollama pull qwen2.5:7b        # General purpose, 7B
ollama pull llama3.2          # Meta's latest, 3B/1B/90B
ollama pull nemotron3-ultra   # NVIDIA's MoE, 55B active
ollama pull deepseek-r1       # Reasoning model
ollama pull phi3.5            # Microsoft, small & fast
ollama pull gemma2:9b         # Google's Gemma 2
ollama pull phi3              # Microsoft's Phi-3
ollama pull mistral:7b        # Mistral's popular model
```

**In Hermes:** `hermes model` → Custom provider → `base_url: http://localhost:11434/v1`

### 3. HuggingFace Free Inference API

- Requires `HF_TOKEN` in `.env` (free tier: 30k req/month)
- Good for: testing open models, embeddings, smaller LLMs
- Not all models support free inference — check model card

### 4. Compare Providers in Hermes

```bash
# Interactive picker shows all configured providers + their models
hermes model

# Set up a new provider
hermes setup model
# or: hermes auth add openrouter  # for API key providers

# Create aliases for quick switching
hermes config set model.aliases.nemotron-free openrouter/nvidia/nemotron-3-ultra:free
hermes config set model.aliases.local-qwen custom/qwen2.5:7b
hermes config set model.aliases.ling-flash openrouter/inclusionai/ling-3.0-flash:free
hermes config set model.aliases.gemma-free openrouter/google/gemma-4-26b-a4b:free
```

## Pitfalls & Gotchas

- **OpenRouter free ≠ unlimited** — sponsored models have rate limits; check model page for details
- **Model IDs differ by provider** — `nemotron-3-ultra` on OpenRouter vs `nemotron3-ultra` on Ollama
- **Context windows vary** — free tiers may have lower limits than paid
- **Tool calling support** — not all free models support function calling; verify before building agents
- **Local needs hardware** — 7B needs ~8GB RAM, 70B+ needs 48GB+; quantize (q4_k_m) to fit
- **Hermes model aliases** — user aliases shadow built-ins; use `provider/model` format for clarity
- **Free model rotation** — sponsored free models may change; periodically re-check availability
- **Latency variance** — free tier models may experience higher latency during peak times

## Verification Steps

After selecting a model:
1. Test with a simple query: `hermes chat -q "Hello" -m <alias>`
2. Check tool calling: `hermes chat -q "Use the terminal tool to run 'echo test'" -m <alias>`
3. Verify context: `hermes chat -q "Summarize this: [paste 50k tokens]" -m <alias>`
4. Check latency: Time a simple request to gauge responsiveness

## References

- `references/openrouter-free-models.md` — Current free model catalog with details from live browse
- `references/local-model-guide.md` — Ollama/LM Studio setup, quantization, hardware sizing
- `references/provider-comparison.md` — Feature matrix across major providers
- `references/openrouter-browse-session.md` — Detailed browsing session notes from research

## Templates

- `templates/model-alias.yaml` — Ready-to-paste aliases for config.yaml
- `templates/provider-setup-checklist.md` — Steps to add a new provider in Hermes
- `templates/ollama-models-list.md` — Common Ollama models for local free inference

## Session-Specific Notes

During this session, we confirmed:
- OpenRouter's free tier includes NVIDIA's Nemotron 3 Ultra (1M context, 2.7T weekly tokens)
- Multiple NVIDIA Nemotron Nano variants are available for free
- Poolside offers programming-specialized free models
- Ling-3.0-flash provides efficient MoE architecture for agentic workflows
- Table view with sorting by weekly tokens helps identify reliable free models