# Python Syntax and Docstring Pitfalls

## Double-Triple-Quote Syntax Error

**What it looks like**:
```
SyntaxError: unterminated string literal (detected at line 66)
```

**The cause**: A docstring written as `"""text.""""` — three opening quotes, text, three closing quotes, then an extra `"`.

Python tokenizes this as:
- `"""` — start of a triple-quoted string
- `text.` — content
- `"""` — end of the triple-quoted string
- `"` — start of a NEW single-quoted string that is never closed

Result: "unterminated string literal" pointing at the extra `"`.

**The fix**: Remove the extra quote. Docstrings are exactly `"""text."""` — three quotes on each side.

**Where it happens**:
- Typing `"""` + text + `"""` and accidentally adding a fourth quote
- Copy-paste errors where the source had an extra quote
- Editing docstrings by adding content at the end and accidentally duplicating the closing `"""`

**How to catch it fast**: Run `python3 -m py_compile script.py` immediately after writing any .py file. The error points to the exact line. No need to execute the script.

## Docstring Formatting

### Triple-quoted docstrings

```python
def foo():
    """This is a docstring."""
    pass
```

Three quotes on each side. No spaces between the quotes and the text (common style, but not required).

### Multi-line docstrings

```python
def foo():
    """First line.

    Second paragraph with more detail.
    """
    pass
```

The closing `"""` can be on its own line (common for multi-line) or after the last line of text.

### Raw docstrings

```python
def foo():
    r"""This is a raw docstring. Backslashes are literal: \n \t."""
    pass
```

Prefix with `r` when the docstring contains backslashes you want to keep literal (regex patterns, Windows paths in examples).

### f-strings in docstrings

Docstrings are NOT f-strings. You cannot use `{variable}` interpolation in a docstring. If you need dynamic content, build the string outside the docstring.

## Other Common Syntax Traps

### Unclosed parentheses/brackets/braces

```python
# ERROR: unclosed parenthesis
def foo(
    x: int
    y: str = "default"  # missing comma AND unclosed (
```

The error message may point to a later line than where the actual error is. Python detects the unclosed delimiter when it reaches the end of the file or finds a token that doesn't fit.

### Indentation errors

```python
# ERROR: inconsistent indentation
def foo():
    x = 1
  y = 2  # wrong indent — mixes spaces and tabs or wrong level
```

Mixing tabs and spaces is a classic cause. Configure your editor to use spaces only (4 spaces per level is the Python standard).

### Missing colon after compound statement

```python
# ERROR: expected ':'
if x > 0
    print(x)
```

Forgetting the `:` after `if`, `for`, `while`, `def`, `class`, `try`, `except`, `finally`, `with`.

### Missing comma in list/dict/tuple

```python
# ERROR: invalid syntax — missing comma
my_list = [
    "item1"
    "item2"  # Python sees "item1" "item2" as adjacent string literals (concat) or error
]
```

In some contexts adjacent string literals concatenate (`"a" "b"` → `"ab"`), but in list/dict literals the missing comma often produces a confusing error on a later line.

### String prefix confusion

```python
# These are all valid but mean different things:
"text"     # regular string
'btext'    # regular string (single quotes)
"""text""" # triple-quoted string (multi-line capable)
r"text"    # raw string
b"text"    # bytes literal
f"text"    # f-string (must have valid Python expressions inside {})
rf"text"   # raw f-string
```

Using `b` prefix with a string that contains non-ASCII characters will raise `SyntaxError` in Python 3.

### Escape sequence misinterpretation

```python
"\n"   # newline (one character)
"\\n"  # literal backslash + n (two characters)
"\t"   # tab
"\\t"  # literal backslash + t
"\x41" # 'A' (hex escape)
```

In regular strings, `\n`, `\t`, `\\`, `\"`, etc. are escape sequences. Use raw strings (`r"..."`) when you want literal backslashes (regex, Windows paths in examples).

## Verification

`python3 -m py_compile script.py` checks syntax without executing. Run it:
- After writing any .py file
- Before trusting a script you just created
- In CI gates for Python code

For import-time checks (ensuring imports resolve, types are consistent), use:

```bash
python3 -c "import py_compile; compile('script.py', 'script.py', 'exec')"
```

Or just run the script with a dry-run flag if it has one.

## See Also

- `python3 -m py_compile` — built-in syntax checker
- [Python Language Reference — Lexical analysis](https://docs.python.org/3/reference/lexical_analysis.html) — official reference for string literals, escapes, and tokenization
