## NYX Repo: Hebbian Learning Reference

**Source**: github.com/jonnysteedman683-wq/NYX

### Plasticity Rules (from `nyx/hebb/rules.py`)
All rules compute Δw from three local signals only:
- `pre[b, i]` — presynaptic activity
- `post[b, j]` — postsynaptic activity  
- `weight[j, i]` — current synapse strength

```
Hebbian:  Δw = η·y·x                     — fire together, wire together (UNSTABLE)
Oja:      Δw = η·y·(x − y·w)             — converges to unit-norm top eigenvector
Instar:   Δw = η·y·(x − w)               — converges to input centroid (online k-means)
BCM:      Δw = η·y·(y − θ)·x, θ=⟨y²⟩    — self-stabilizing, sliding threshold
```

### CompetitiveHebbianLayer (from `nyx/hebb/layers.py`)
1. Compute similarity: `-||x - w_j||²` (distance) or `w_j^T x` (dot)
2. Lateral inhibition: keep top-k units, normalize to sum=1
3. Conscience bias: penalize units winning > fair share (prevents collapse)
4. Learning: apply plasticity rule to (x, h_plastic)

Key: conscience gates *plasticity*, not *transmission*. Train and test outputs differ.

### HebbNet (from `nyx/hebb/model.py`)
```
x → [CompetitiveLayer] → h → [DeltaReadout] → logits
```
- Hidden layer: unsupervised, never sees labels
- Readout: supervised by locally observable error (target - output)
- Optional global modulator (3-factor rule): one scalar broadcast to all hidden synapses
- `model.parameters()` returns empty list — nothing for an optimizer to touch

### Porting Notes
- PyTorch `register_buffer` → plain numpy arrays (no gradient graph)
- `torch.cdist` → manual broadcast: `x[:,None,:] - weight[None,:,:]`
- `scatter_` (top-k) → `np.put_along_axis`
- `torch.no_grad()` → not needed (all updates are manual)
- BCM needs per-unit `theta` buffer + `tau` time constant
