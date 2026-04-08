# Type Checking Guide

This project uses **mypy** for static type checking to catch type safety issues at development time.

## Setup

### Installation

Type checking dependencies are included in the dev dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- `mypy>=1.7` - Static type checker
- `pytest>=7.0` - Testing framework  
- `pytest-asyncio` - Async test support
- `ruff` - Linter and formatter

### Configuration

Type checking is configured in `pyproject.toml` under `[tool.mypy]`:

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
disallow_untyped_defs = false
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
```

## Running Type Checks

### Check all files

```bash
mypy .
```

### Check specific file or directory

```bash
mypy core/github_client.py
mypy agents/
mypy tests/
```

### Check with verbose output

```bash
mypy --verbose .
```

### Check and show detailed error information

```bash
mypy --show-error-codes --show-error-context .
```

## Type Annotations Guide

### Basic Function Annotations

```python
def add(a: int, b: int) -> int:
    return a + b

def process(name: str) -> None:
    """Functions with no return use None."""
    print(name)

def parse_number(value: str) -> int | None:
    """Use PEP 604 union syntax (Python 3.10+)."""
    try:
        return int(value)
    except ValueError:
        return None
```

### Collection Types

```python
from typing import list, dict, set

def process_ids(ids: list[int]) -> dict[int, str]:
    """Use subscript syntax for generic types."""
    return {id: f"item_{id}" for id in ids}
```

### Optional Parameters

```python
def configure(debug: bool = False, config_path: str | None = None) -> None:
    """Use | None for optional parameters."""
    ...
```

### TypedDict for Structured Data

```python
from typing import TypedDict

class UserData(TypedDict):
    """Use TypedDict for dict with known keys."""
    id: int
    name: str
    email: str | None

def process_user(user: UserData) -> str:
    return f"{user['name']} ({user['id']})"
```

### Return Types from GitHub API

This project includes TypedDict definitions for GitHub API responses:

```python
from core.models import PRData, IssueData, ReleaseData, RepoStats

def analyze_pr(pr_number: int) -> None:
    client = GitHubClient()
    pr: PRData = client.get_pr(pr_number)
    
    # Type checker knows these fields exist:
    print(pr["title"])
    print(pr["author"])
    print(pr["diff_stats"]["additions"])
```

### Generic Functions

```python
from typing import TypeVar, Callable

T = TypeVar("T")

def retry(fn: Callable[..., T], max_attempts: int = 3) -> T:
    """Generic function that returns same type as input function."""
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception:
            if attempt == max_attempts - 1:
                raise
```

### Ignoring Type Errors

Use `# type: ignore` only when absolutely necessary:

```python
# For external libraries without type hints
import mellea  # type: ignore

# For specific line issues
value: str = get_untyped_value()  # type: ignore[assignment]
```

## Type Safety Best Practices

### DO

✅ **Annotate all function parameters and returns**
```python
def process_data(items: list[str]) -> dict[str, int]:
    ...
```

✅ **Use TypedDict for structured dictionaries**
```python
class Config(TypedDict):
    api_key: str
    timeout: int
```

✅ **Use Union types or `|` syntax for optional values**
```python
result: str | None = get_result()
```

✅ **Use Generic types for reusable functions**
```python
T = TypeVar("T")
def wrap_result(data: T) -> tuple[T, timestamp]:
    ...
```

### DON'T

❌ **Use bare `Any` type**
```python
# Bad
def process_item(item: Any) -> Any:
    ...

# Good
def process_item(item: dict[str, Any]) -> str:
    ...
```

❌ **Mix typed and untyped code**
```python
# Bad
def calculate(x, y) -> int:  # Parameters untyped
    return x + y

# Good  
def calculate(x: int, y: int) -> int:
    return x + y
```

❌ **Ignore type errors without documentation**
```python
# Bad
value: str = 123  # type: ignore

# Good - document why
# External API returns incorrect type
value: str = external_api_call()  # type: ignore[assignment]
```

## Common Type Errors and Fixes

### Error: Incompatible types in assignment

```python
# Error: Incompatible types in assignment (expression has type "int", variable has type "str")
value: str = 42  # ❌

# Fix
value: int = 42  # ✅
```

### Error: Missing return type annotation

```python
# Error: Function is missing a return type annotation
def process(data):  # ❌
    return data

# Fix
def process(data: dict) -> dict:  # ✅
    return data
```

### Error: Argument of type "None" cannot be assigned to parameter

```python
# Error: Argument 1 to "print" has incompatible type "str | None"; expected "str"
value: str | None = get_value()
print(value)  # ❌

# Fix - use type guard
value: str | None = get_value()
if value is not None:
    print(value)  # ✅
```

## CI/CD Integration

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
mypy . --ignore-missing-imports
if [ $? -ne 0 ]; then
    echo "Type checking failed"
    exit 1
fi
```

### GitHub Actions

Add to `.github/workflows/test.yml`:

```yaml
- name: Type check
  run: |
    pip install -e ".[dev]"
    mypy .
```

## Troubleshooting

### "error: Cannot find implementation or library stub for module"

This means mypy can't find the module. Add to `pyproject.toml`:

```toml
[tool.mypy]
ignore_missing_imports = true
```

Or create a `py.typed` marker file in the package.

### "error: Need type annotation for variable"

Provide explicit type:

```python
# Error
items = []  # ❌

# Fix
items: list[str] = []  # ✅
```

### "error: No attribute" 

TypedDict or class is missing an attribute. Check spelling and ensure all required fields are present.

## Related Files

- [pyproject.toml](pyproject.toml) — Type checking configuration
- [core/models.py](core/models.py) — TypedDict definitions for API responses
- [core/github_client.py](core/github_client.py) — Example of properly typed API client

## Resources

- [mypy Documentation](https://mypy.readthedocs.io/)
- [PEP 484 — Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 604 — Union Types](https://www.python.org/dev/peps/pep-0604/)
- [TypedDict Documentation](https://docs.python.org/3.8/library/typing.html#typing.TypedDict)
