# OpenGL Renderer — Pyglet + ModernGL

## Architecture

```
gl_renderer.py — Main renderer class (GLRenderer)
  ├─ _build_terrain() — static mesh from biome data
  ├─ _build_agent_buffers() — instanced circle rendering
  ├─ _build_particle_buffers() — GL_POINTS particle system
  ├─ _build_quad() — fullscreen quad for post-processing
  ├─ update(dt) — tick simulation, update buffers
  ├─ _update_particles(dt) — particle life decay + drift
  ├─ _spawn_particles(x, y, color, count)
  └─ render() — clear, draw terrain, agents, particles

gl.py — Entry point with --load flag
```

## Shader Programs

### Terrain
- Vertex: transforms position by orthographic projection, passes color
- Fragment: outputs flat color (no lighting)

### Agents
- Vertex: instanced — each agent is a unit circle offset by position, scaled by size
- Fragment: circular shape with soft edge + glow effect (`exp(-dist * 4.0) * 0.5`)

### Particles
- Vertex: GL_POINTS with life-based point size (`3.0 + life * 5.0`)
- Fragment: circular with life-based alpha, color boosted by life

### Bloom (post-processing)
- Vertex: fullscreen quad pass-through
- Fragment: samples 5x5 neighborhood, blends with original via `u_bloom_strength`

## Buffer Layout

### Terrain mesh
```
vertices: [x0, y0, x1, y1, ...]  — 4 vertices per cell (quad)
colors:   [r0, g0, b0, r1, g1, b1, ...]  — per-vertex color
indices:  [0, 1, 2, 0, 2, 3, ...]  — 2 triangles per quad
```

### Agent buffers (instanced)
```
circle_vbo:    [cos(θ), sin(θ)] × 16 segments  — unit circle
offset_vbo:    [x, y] × N agents  — per-instance position
color_vbo:     [r, g, b] × N agents  — per-instance color
size_vbo:      [size] × N agents  — per-instance radius
```

### Particle buffer
```
particles: [x, y, r, g, b, life] × 1000 particles
```

## Pyglet Config

On Windows, must request OpenGL 3.3 core profile:
```python
config = pyglet.gl.Config(major_version=3, minor_version=3, double_buffer=True, samples=4)
```

Default config may give legacy context that doesn't support GLSL 330.

## Dependencies

```bash
pip install pyglet moderngl
```

- `pyglet` — window creation, event loop, GL context
- `moderngl` — Pythonic OpenGL wrapper, shader compilation, buffer management
- `glcontext` — backend for moderngl (auto-installed)
