# ARISE Porting Examples

## AQB rl-core.ts → NumPy (TypeScript → Python)

### Dense layer with backprop
Source: `rl-core.ts` Dense class with `forward()` and `backward()`.
Target: `arise/brain.py` Dense class using numpy matmul + manual gradient computation.

Key differences:
- TS uses 2D arrays `number[][]`, NumPy uses `np.ndarray` with explicit dtype
- TS `matmul` is manual triple loop, NumPy uses `@` operator
- TS `randn` uses Box-Muller transform, NumPy uses `np.random.randn`
- Backward pass identical math: `grad_W = x.T @ grad_y`, `grad_x = grad_y @ W.T`

### QNetwork (3-layer with ReLU)
Source: `rl-core.ts` QNetwork with fc1→fc2→out, ReLU activations, CQL penalty.
Target: `arise/brain.py` QNetwork, simplified (no CQL for now).

Key: ReLU mask must be cached during forward and applied during backward:
```python
h = fc1.forward(x)
mask1 = (h > 0).astype(np.float32)
h = h * mask1
# backward:
grad_h = grad_h * mask1  # apply cached mask
```

### ICM Curiosity Module
Source: `rl-core.ts` Encoder + ForwardModel + InverseModel.
Target: `arise/brain.py` ICM class.

Ported all three sub-networks. Intrinsic reward = prediction error of forward model:
```python
pred_enc_next = forward_model.forward(enc_state, action_onehot)
error = np.sum((pred_enc_next - enc_next) ** 2)
intrinsic_reward = error * 0.1
```

## NYX Hebbian → NumPy (PyTorch → Python)

### CompetitiveHebbianLayer
Source: `nyx/hebb/layers.py` CompetitiveHebbianLayer (PyTorch nn.Module).
Target: `arise/hebbian.py` CompetitiveLayer (plain Python class).

Key differences:
- PyTorch `register_buffer` → NumPy instance attributes
- `torch.cdist` → manual: `-np.sum((x[:,None,:] - weight[None,:,:])**2, axis=-1)`
- `topk` → `np.argpartition(-s, k, axis=1)[:k]`
- `scatter_` → `np.put_along_axis`
- `softmax` with temperature: `np.exp((top_val - top_val[:,:1]) / temperature)`

### Plasticity Rules
Source: `nyx/hebb/rules.py` — Hebbian, Oja, Instar, BCM.
Target: `arise/hebbian.py` — same 4 rules as standalone functions.

Each rule computes `Δw` from three local signals only: `pre`, `post`, `weight`.
- Hebbian: `Δw = η·y·x` (unstable, diverges)
- Oja: `Δw = η·y·(x − y·w)` (converges to top eigenvector)
- Instar: `Δw = η·y·(x − w)` (converges to input centroid)
- BCM: `Δw = η·y·(y − θ)·x` with sliding threshold (self-stabilizing)

### DeltaReadout
Source: `nyx/hebb/layers.py` DeltaReadout.
Target: `arise/hebbian.py` DeltaReadout.

Simple linear readout with delta-rule learning: `Δw = η·(target - output)·pre`
No backward pass needed — error is directly observable at the output.
