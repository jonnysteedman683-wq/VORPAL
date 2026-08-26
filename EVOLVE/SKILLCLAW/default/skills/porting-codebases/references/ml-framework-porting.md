---
name: port-ml-across-frameworks
description: "Use when porting neural net code between frameworks."
---
# Porting ML Code Across Frameworks

When porting neural network code between frameworks (e.g. PyTorch → NumPy, TypeScript → Python), follow this pattern.

## Step-by-step

1. **Read the source architecture fully** — understand every layer, activation, loss, and training loop before writing any target code.

2. **Map primitives first** — identify the framework-specific primitives and their equivalents:
   - `torch.Tensor` → `numpy.ndarray` (dtype must be explicit: `.astype(np.float32)`)
   - `nn.Linear` → manual `x @ W + b` with Xavier init: `np.random.randn(in, out) * np.sqrt(2/in)`
   - `nn.Module` → plain Python class with `__init__` + methods
   - `register_buffer` → instance attributes (no parameter/optimizer distinction in NumPy)
   - `torch.no_grad()` → not needed (NumPy has no autograd)
   - `tf.tidy()` → not needed (NumPy has no graph)
   - `softmax` → `np.exp(x - x.max()) / np.exp(x - x.max()).sum()`
   - `cdist` → manual: `np.sqrt(((a[:,None,:]-b[None,:,:])**2).sum(-1))`
   - `scatter_` → `np.put_along_axis` or manual indexing

3. **Port layers bottom-up** — start with the lowest-level building blocks (Dense, activations), verify each with a shape test, then compose into networks.

4. **Preserve the math, not the API** — don't try to replicate PyTorch's API surface. Write idiomatic target-framework code that computes the same thing.

5. **Handle stateful layers carefully** — layers with buffers (running averages, thresholds, win rates) need explicit attribute copying during `copy()` and `mutate()`.

6. **Test shape parity first** — before testing correctness, verify every layer's input/output shapes match the source. Shape bugs are the #1 failure mode.

7. **Test numerical parity second** — for deterministic operations (forward pass with fixed weights), verify outputs match within float32 tolerance (~1e-5).

## Pitfalls

- **Float precision**: PyTorch defaults to float32, TensorFlow to float32, but NumPy defaults to float64. Always explicitly set `dtype=np.float32` to match source behavior.
- **Batch dimension**: PyTorch/TensorFlow always have a batch dim. NumPy code often works with single samples. Always handle `ndim == 1` by reshaping to `(1, -1)`.
- **Softmax stability**: Must subtract max before exp to prevent overflow. PyTorch does this internally; NumPy doesn't.
- **Weight init**: PyTorch's default Kaiming/Xavier init matters for training stability. Replicate it: `np.random.randn(in, out) * np.sqrt(2.0 / in)`.
- **Mutation vs gradient**: When porting evolutionary (genetic) code, `mutate()` adds noise to weights. When porting gradient-based code, `backward()` updates weights via gradient descent. Don't confuse the two.
- **Copy semantics**: NumPy arrays are mutable. `copy()` must do deep copy (`arr.copy()`), not reference copy, or mutations will corrupt the parent.
- **ICM deserialization stubs**: When reconstructing objects with `__new__`, the stub class must have actual methods (not just attributes). Use the real class's `__new__`, not a bare `type()` call.

## Reference Files
- `references/arise-ports.md` — concrete porting examples from ARISE (AQB TypeScript→NumPy, NYX PyTorch→NumPy)
- `references/economy-tuning.md` — agent simulation economy balancing patterns and tuning principles

## Example: PyTorch Dense → NumPy

```python
# PyTorch
class Dense(nn.Module):
    def __init__(self, in_dim, out_dim):
        self.linear = nn.Linear(in_dim, out_dim)
    def forward(self, x):
        return F.relu(self.linear(x))

# NumPy
class Dense:
    def __init__(self, in_dim, out_dim, lr=0.001):
        self.W = np.random.randn(in_dim, out_dim).astype(np.float32) * np.sqrt(2.0/in_dim)
        self.b = np.zeros(out_dim, dtype=np.float32)
    def forward(self, x):
        self._x = x  # cache for backward
        return np.maximum(0, x @ self.W + self.b)  # relu
    def backward(self, grad_y):
        grad_W = self._x.T @ grad_y
        grad_b = grad_y.sum(axis=0)
        grad_x = grad_y @ self.W.T
        self.W -= self.lr * grad_W
        self.b -= self.lr * grad_b
        return grad_x
```
