---
name: porting-codebases
description: "Port code across languages, repos, and ML frameworks (TS→Python, PyTorch→NumPy)."
---
# Porting Code Between Codebases — Umbrella

Sub-topics (load with `skill_view(name, file_path)`):
- `references/ts-to-python-porting.md` — TypeScript/JS → Python/NumPy workflow
- `references/ml-framework-porting.md` — porting neural nets across ML frameworks (PyTorch/TF/NumPy)
- `references/nyx-architecture.md`, `references/nyx-hebbian.md` — NYX Hebbian net internals
- `references/suprime-swarm.md` — SUPRIME swarm port notes
- `references/arise-ports.md`, `references/economy-tuning.md` — ARISE port + tuning records

## Pattern: Cross-Language Port
When porting from TypeScript/JS to Python (or vice versa):

1. **Read the full source first** — don't port piecemeal. Understand the architecture before translating
2. **Map data structures first** — TS classes → Python dataclasses, TS arrays → numpy arrays
3. **Port the math, not the framework** — strip React/tensorflow/torch wrappers, keep the core algorithms
4. **Preserve the interface** — same method names, same parameter order, same return shapes
5. **Test immediately after each module** — don't port 5 files then test

## AQB → ARISE Porting Map
| AQB (TypeScript) | ARISE (Python/NumPy) | Notes |
|---|---|---|
| `Dense` class with `forward/backward` | Same, numpy matmul | `W` is (in, out), bias is (out,) |
| `QNetwork` with 3 Dense layers | Same architecture | ReLU between layers, linear output |
| `Encoder` (Dense + ReLU) | Same | Used in ICM curiosity |
| `ForwardModel` (concat enc+action → predict next) | Same | Concatenate along last axis |
| `InverseModel` (concat enc+enc_next → predict action) | Same | Split gradient at concat point |
| `ReplayBuffer` | Same | Simple list with random sampling |

## NYX → ARISE Porting Map
| NYX (PyTorch) | ARISE (NumPy) | Notes |
|---|---|---|
| `nn.Module` buffers | Plain numpy arrays | No gradient graph needed |
| `torch.Tensor` operations | numpy equivalents | `@` for matmul, `*` for elementwise |
| `torch.no_grad()` context | Not needed | All Hebbian updates are manual |
| `scatter_` (top-k selection) | `np.put_along_axis` | For lateral inhibition |
| `cdist` (pairwise distance) | Manual broadcast | `x[:,None,:] - weight[None,:,:]` |
| Plasticity rules | Standalone functions | `delta(pre, post, weight, lr)` |

## Pitfalls
- **Don't port the framework, port the math** — strip React/tensorflow/torch wrappers
- **Float precision**: TS uses float64, numpy defaults to float64, PyTorch uses float32. Match explicitly with `.astype(np.float32)`
- **Batch dimension**: PyTorch always has batch dim. NumPy code should handle both (1,) and (N,) inputs
- **Biome assignment bug**: when assigning biomes from thresholds, go HIGHEST to LOWEST. Going lowest-to-highest overwrites all values with the last threshold
- **Economy balance**: hunger_per_tick must be low enough that agents can earn currency before dying. Test with `for _ in range(500): sim.tick()` and check population doesn't crash
