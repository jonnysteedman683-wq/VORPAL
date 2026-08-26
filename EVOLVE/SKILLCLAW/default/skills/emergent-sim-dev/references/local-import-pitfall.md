# Local Import Pitfall in Python

## The Bug

When a name is imported at module level AND re-imported inside a function, Python treats
the local import as creating a **local variable** that shadows the module-level one.

This causes `UnboundLocalError` when code in the same function uses the name BEFORE
the local import line executes.

## Example

```python
# Module level (line 18)
from .world import World, wrap_x, wrap_y, toroidal_distance

# Inside _social_tick() (line 650)
if interpreted == 4:  # CALL
    from .world import toroidal_distance  # WRONG — shadows module-level
    d = toroidal_distance(self.x, self.y, sig.x, sig.y)  # works here

# But earlier in the same function (line 580):
d = toroidal_distance(x, y, other.x, other.y)  # UnboundLocalError!
```

Python sees `toroidal_distance` as a local variable (due to the import at line 650),
but the assignment hasn't happened yet when line 580 executes.

## The Fix

**Never re-import module-level names inside functions.** If `from .world import toroidal_distance`
exists at module level, just use `toroidal_distance(...)` directly everywhere in the file.

Same applies to `SocialEdge` — if it's defined in the same file (`agent.py`), don't
`from .agent import SocialEdge` inside a method. Just use `SocialEdge(...)`.

## How to detect

```bash
# Find all local re-imports
grep -n "from .world import toroidal_distance" arise/agent.py
# Should return exactly 1 line (the module-level import)
# If more, remove the local ones

# Same for self-imports
grep -n "from .agent import" arise/agent.py
# Should return 0 lines (it's the same file!)
```

## Real incident

In ARISE, adding call & response to `_social_tick()` introduced a local
`from .world import toroidal_distance` inside the CALL handler. This caused
`UnboundLocalError` when the earlier code path (leader following) tried to use
`toroidal_distance` before the CALL handler's import line was reached.
