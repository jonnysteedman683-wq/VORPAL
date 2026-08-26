# Terrain Generation Patterns

## Multi-octave noise with scipy

```python
from scipy.ndimage import gaussian_filter, zoom

def _smooth_noise(width, height, scale, seed):
    rng = np.random.RandomState(seed)
    coarse_w = max(2, width // scale)
    coarse_h = max(2, height // scale)
    coarse = rng.randn(coarse_h, coarse_w).astype(np.float32)
    upsampled = zoom(coarse, (height/coarse_h, width/coarse_w), order=1)
    smooth = gaussian_filter(upsampled, sigma=scale/4.0)
    smooth = (smooth - smooth.min()) / (smooth.max() - smooth.min() + 1e-8)
    return smooth

# 3 octaves for height
h1 = _smooth_noise(w, h, scale=8, seed=seed)       # large features
h2 = _smooth_noise(w, h, scale=4, seed=seed+1)     # medium detail
h3 = _smooth_noise(w, h, scale=2, seed=seed+2)     # fine detail
heightmap = h1*0.6 + h2*0.3 + h3*0.1
```

## Biome assignment (CORRECT — high to low)

```python
# WRONG: iterates low→high, last threshold overwrites all
for i, threshold in enumerate(thresholds):
    biome_map[combined < threshold] = i  # BUG!

# CORRECT: iterates high→low
biome_map = np.full((h, w), len(thresholds)-1, dtype=np.int32)
for i in range(len(thresholds)-1, -1, -1):
    biome_map[combined < thresholds[i]] = i
```

## River carving (downhill gradient descent)

```python
def generate_rivers(heightmap, n_rivers=5, seed=None):
    rng = np.random.RandomState(seed)
    h, w = heightmap.shape
    river_pixels = set()
    
    for _ in range(n_rivers):
        # start from high point
        while True:
            sx, sy = rng.randint(0, w), rng.randint(0, h)
            if heightmap[sy, sx] > 0.6:
                break
        
        x, y = sx, sy
        for step in range(300):
            river_pixels.add((x, y))
            # find lowest neighbor
            best_h = heightmap[y, x]
            best_dx, best_dy = 0, 0
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = (x+dx)%w, (y+dy)%h
                if heightmap[ny, nx] < best_h:
                    best_h = heightmap[ny, nx]
                    best_dx, best_dy = dx, dy
            if best_dx == 0 and best_dy == 0:
                break
            x, y = (x+best_dx)%w, (y+best_dy)%h
            # widen downstream
            if step > 50:
                river_pixels.add((x+1, y))
                river_pixels.add((x, y+1))
    
    return river_pixels
```

## Biome types (11 biomes)

| Biome | Height | Moisture | Temp | Speed | Passable |
|-------|--------|----------|------|-------|----------|
| Deep Water | <0.20 | any | any | 0.0 | No |
| Shallow | 0.20-0.28 | any | any | 0.3 | Yes |
| Beach | 0.28-0.32 | any | any | 0.9 | Yes |
| Plains | 0.32-0.72 | <0.4 | any | 1.0 | Yes |
| Forest | 0.32-0.72 | >0.4 | any | 0.6 | Yes |
| Jungle | 0.32-0.72 | >0.6 | >0.5 | 0.4 | Yes |
| Swamp | 0.32-0.45 | >0.7 | any | 0.35 | Yes |
| Desert | 0.32-0.72 | <0.25 | >0.5 | 1.1 | Yes |
| Tundra | 0.32-0.72 | any | <0.25 | 0.5 | Yes |
| Highlands | 0.72-0.85 | any | any | 0.7 | Yes |
| Mountain | >0.85 | any | any | 0.0 | No |
| River | any | any | any | 0.0 | No |

## Performance

- Cache terrain as a pygame.Surface (render once, blit each frame)
- Use `cell_size=4` for terrain pixels (4x4 blocks)
- Rivers stored as set of (x,y) tuples — fast lookup with `in`
