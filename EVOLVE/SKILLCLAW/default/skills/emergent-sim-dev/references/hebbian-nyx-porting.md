# Porting NYX Hebbian Rules to NumPy

Source: https://github.com/jonnysteedman683-wq/NYX/tree/main/nyx/hebb

## Key Files
- `rules.py` — 4 plasticity rules (Hebbian, Oja, Instar, BCM)
- `layers.py` — CompetitiveHebbianLayer + DeltaReadout
- `model.py` — HebbNet (stack of competitive layers + delta readout)

## Conversion Reference

### Rule Formulas (identical in both languages)
```
Hebbian:  Δw = η·y·x
Oja:      Δw = η·y·(x − y·w)
Instar:   Δw = η·y·(x − w)
BCM:      Δw = η·y·(y − θ)·x,  θ = ⟨y²⟩ (sliding threshold)
```

### PyTorch → NumPy Patterns
```python
# PyTorch: self.register_buffer("weight", torch.randn(n, m) * scale)
self.weight = np.random.randn(n, m).astype(np.float32) * scale

# PyTorch: h = torch.exp((top_val - top_val[:, :1]) / self.temperature)
resp = np.exp((top_val - top_val[:, :1]) / self.temperature)

# PyTorch: h.scatter_(1, top_idx, resp)
h = np.zeros_like(s)
np.put_along_axis(h, top_idx, resp, axis=1)

# PyTorch: @torch.no_grad() — just don't call .backward()
```

### Conscience Bias (critical for competitive learning)
```python
# Scale bias by gap between best and last surviving unit
top = np.argpartition(-s, k+1, axis=1)[:, :k+1]
top_vals = np.take_along_axis(s, top, axis=1)
gap = max(float(top_vals[:, 0].mean() - top_vals[:, -1].mean()), _EPS)
over = (self.win_rate - 1.0 / self.n_units) * self.n_units
s = s - self.conscience * gap * over
```

### BCM Sliding Threshold
```python
# Update threshold toward current mean-square activity
mean_sq = (post * post).mean(axis=0)
self.theta = self.theta * (1 - 1/self.tau) + mean_sq / self.tau
```

## Integration Pattern
- HebbNet has `N_ACTIONS` matching Brain.N_ACTIONS
- `think(state)` → returns action index (same interface as Brain)
- `learn(state, action, reward, next_state)` → returns 0.0 (no intrinsic reward)
- `mutate(rate)` → returns mutated copy (same as Brain)
- Default n_actions must match current action count (update when adding actions)
