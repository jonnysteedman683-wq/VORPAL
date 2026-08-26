# NYX — Experimental Neural Architectures

Repo: https://github.com/jonnysteedman683-wq/NYX
Stack: Python, PyTorch
Stars: 1 (but high quality, well-documented)

## Two Architectures

### Part I — KAN (Kolmogorov-Arnold Network)
- No weight matrices, no activation functions on nodes
- Every learnable parameter is a **univariate B-spline function on an edge**
- Nodes only sum: `y_j = Σ_i φ_ij(x_i)`
- Each edge function: `φ_ij(x) = m_ij * [s^b_ij * b(x) + s^s_ij * Σ_m c_ijm * B_m(x)]`
- B-spline coefficients are learnable, grid can be refined during training
- Key files: `nyx/layer.py`, `nyx/bspline.py`, `nyx/model.py`, `nyx/train.py`

### Part II — HebbNet (No-Backprop Learning)
- Network learns during forward pass only — no backward pass, no gradients
- Hidden layer: **CompetitiveHebbianLayer** (unsupervised, lateral inhibition)
- Readout: **DeltaReadout** (supervised, locally observable error)
- Optional global scalar modulator gates hidden plasticity (three-factor rule)
- Key files: `nyx/hebb/layers.py`, `nyx/hebb/rules.py`, `nyx/hebb/model.py`

## Plasticity Rules (nyx/hebb/rules.py)

All rules compute Δw from three local signals only: pre, post, weight.

```python
# Hebbian: Δw = η·y·x (unstable — diverges)
# Oja: Δw = η·y·(x − y·w) (converges to top eigenvector, online PCA)
# Instar: Δw = η·y·(x − w) (converges to input centroid, online k-means)
# BCM: Δw = η·y·(y − θ)·x, θ = ⟨y²⟩ (self-stabilizing, sliding threshold)
```

## CompetitiveHebbianLayer
- Units compete for inputs through lateral inhibition
- Winners adapt toward what activated them
- **Conscience bias**: penalizes units winning more than fair share (prevents collapse)
- Similarity: distance-based (`-‖x - w_j‖²`) or dot-product (`w_j^T x`)
- Weights are **buffers, not parameters** — `model.parameters()` returns empty list

## Porting Notes
- NYX uses PyTorch; for ARISE we need NumPy equivalents
- B-spline math in `nyx/bspline.py` is pure tensor ops — straightforward to port
- CompetitiveHebbianLayer needs careful porting of the lateral inhibition (top-k selection + normalization)
- BCM's sliding threshold (`theta`) is stateful — needs to persist across forward calls
