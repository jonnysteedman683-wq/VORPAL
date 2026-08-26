---
name: ts-to-python-porting
description: "Use when porting TypeScript ML/RL code to Python/NumPy."
---
# TypeScript → Python/NumPy Porting Patterns

Reusable patterns for porting neural network and RL code from TypeScript to Python/NumPy, based on successful ports from ARCANE QUANTUM BRAIN and NYX repos.

## Dense Layer
TS `Dense` class with `forward(x)` / `backward(grad_y)` → Python equivalent:
- `self.W = np.random.randn(in_dim, out_dim).astype(np.float32) * np.sqrt(2.0 / in_dim)`
- Forward: `x @ self.W + self.b`
- Backward: `grad_W = self._x.T @ grad_y`, `grad_b = grad_y.sum(axis=0)`, `grad_x = grad_y @ self.W.T`
- Always store `self._x` in forward for backward pass

## QNetwork (3-layer)
TS `QNetwork` with ReLU + CQL → Python:
- Layers: `fc1(ReLU) → fc2(ReLU) → out(linear)`
- Store masks: `self._mask1 = (h > 0).astype(np.float32)` for backward
- Train step: MSE loss on `(q[action] - target_q)`, gradient through masks

## ICM Curiosity Module
TS `Encoder + ForwardModel + InverseModel` → Python:
- Encoder: `Dense → ReLU` (store mask for backward)
- ForwardModel: `concat(enc_s, a_onehot) → Dense → ReLU → Dense`
- InverseModel: `concat(enc_s, enc_s_next) → Dense → ReLU → Dense`
- Intrinsic reward: `sum((pred_enc_next - enc_s_next)²) * 0.1`

## Pitfalls
- TS uses `number[][]` (row-major arrays); NumPy uses same convention but watch batch dimension
- TS `matmul` is manual triple loop; NumPy uses `@` operator
- TS `relu` returns `{out, mask}`; in NumPy compute mask separately: `(x > 0).astype(np.float32)`
- Serialization: `__new__()` + assign attributes (don't call `__init__` — it re-initializes weights)
- Float precision: TS uses float64 by default; NumPy should use float32 for speed
- JSON round-trip: float32→JSON→float64→float32 causes ~1e-6 drift (acceptable)

## Hebbian Plasticity Rules (from NYX)
Four local learning rules, no backprop needed:
- **Hebbian**: `Δw = η·y·x` — unstable, diverges along top eigenvector
- **Oja**: `Δw = η·y·(x − y·w)` — converges to unit-norm top eigenvector (online PCA)
- **Instar**: `Δw = η·y·(x − w)` — converges to input centroid (online k-means)
- **BCM**: `Δw = η·y·(y − θ)·x, θ = ⟨y²⟩` — self-stabilizing, experimentally supported in visual cortex

Competitive layer: lateral inhibition (keep top-k), conscience bias (fair-share win rate).

## Hybrid Brain (QNet + HebbNet)
Combine both brain types in one agent:
- QNet handles strategic actions (task selection, trade, build)
- HebbNet handles fast reactions (foraging, fleeing, movement)
- Blend factor (0-1) controls influence: 0 = pure QNet, 1 = pure HebbNet
- Fast actions (move, forage) bias toward HebbNet (blend * 0.7 + 0.3)
- Strategic actions (task, trade, build) bias toward QNet (blend * 0.3)
- Created when QNet and HebbNet agents reproduce near each other (40% chance)
- Blend factor mutates ±0.1 per generation
