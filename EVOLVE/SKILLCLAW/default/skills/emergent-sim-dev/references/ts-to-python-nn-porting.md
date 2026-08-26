# TypeScript → Python Neural Network Porting Reference

Ported from ARCANE QUANTUM BRAIN (`src/lib/rl-core.ts`) to ARISE (`arise/brain.py`).

## Architecture Mapping

| TypeScript (rl-core.ts) | Python (brain.py) |
|---|---|
| `Dense` class with manual matmul | `Dense` class with numpy `@` |
| `QNetwork` (fc1→fc2→out, ReLU) | `QNetwork` (fc1→fc2→out, ReLU) |
| `Encoder` (Dense + ReLU) | `Encoder` (Dense + ReLU) |
| `ForwardModel` (concat→fc1→fc2) | `ForwardModel` (concat→fc1→fc2) |
| `InverseModel` (concat→fc1→fc2) | `InverseModel` (concat→fc1→fc2) |
| `ReplayBuffer` (array push/shift) | `ReplayBuffer` (list push/pop(0)) |
| `CuriousAgent` (DQN + ICM + HRL) | `Brain` (Q-learning + ICM + mutation) |

## Key Conversion Patterns

### Matrix Operations
```typescript
// TypeScript: manual triple loop
for (let i = 0; i < m; i++)
  for (let k = 0; k < n; k++)
    for (let j = 0; j < p; j++)
      C[i][j] += A[i][k] * B[k][j];
```
```python
# Python: numpy @
C = A @ B
```

### Initialization
```typescript
// TypeScript: Xavier-ish
this.W = randn(in_dim, out_dim); // gaussian * 1.0
```
```python
# Python: He initialization
self.W = np.random.randn(in_dim, out_dim) * np.sqrt(2.0 / in_dim)
```

### Activation Functions
```typescript
// TypeScript: manual relu with mask
function relu(x) {
  const out = zeros(m, n);
  const mask = zeros(m, n);
  for (let i = 0; i < m; i++)
    for (let j = 0; j < n; j++)
      if (x[i][j] > 0) { out[i][j] = x[i][j]; mask[i][j] = 1.0; }
  return { out, mask };
}
```
```python
# Python: numpy maximum
h = np.maximum(0, x)
mask = (h > 0).astype(np.float32)
```

### Backward Pass
```typescript
// TypeScript: manual gradient computation
const grad_W = matmul(transpose(this.x), grad_y);
const grad_b = sum_along_axis0(grad_y);
const grad_x = matmul(grad_y, transpose(this.W));
this.W[i][j] -= this.lr * grad_W[i][j];
```
```python
# Python: numpy operations
grad_W = self._x.T @ grad_y
grad_b = grad_y.sum(axis=0)
grad_x = grad_y @ self.W.T
self.W -= self.lr * grad_W
```

### Batch Operations
```typescript
// TypeScript: array of arrays
const states = batch.map(b => b[0]); // number[][]
```
```python
# Python: numpy 2D array
states = np.array([buffer[i][0] for i in indices])  # (batch, state_dim)
```

## Key Differences

1. **No tensor disposal needed** — numpy handles memory automatically (no tf.tidy())
2. **No async** — numpy operations are synchronous
3. **Broadcasting** — numpy broadcasts automatically for bias addition
4. **Slicing** — numpy slicing is more powerful (`x[:, :dim]` vs `row.slice(0, dim)`)
5. **Copy semantics** — numpy arrays need explicit `.copy()` to avoid aliasing

## What Was NOT Ported

- **HRL Options** — too complex for initial prototype, can add later
- **Active Inference** — requires world model + preference manager, future work
- **CQL (Conservative Q-Learning)** — offline RL penalty, not needed for online sim
- **Firebase persistence** — replaced with in-memory only
