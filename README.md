# symref

Refactor-safe forward references for Python dotted import paths.

Many frameworks (Celery, Django, etc.) accept dotted string paths as configuration. These strings are invisible to refactoring tools and IDEs -- renaming a module silently breaks them. `symref` wraps these paths in a `str` subclass that registers them for later validation, catching broken references in tests instead of production.

## Installation

```bash
pip install symref
```

Requires Python 3.12+. No runtime dependencies.

## Usage

```python
from symref import ref

app.conf.task_routes = {
    ref("myapp.tasks.send_email", kind="celery_task"): {"queue": "email"},
    ref("myapp.tasks.process_order", kind="celery_task"): {"queue": "orders"},
}
```

`ref()` returns a plain `str` -- frameworks see no difference. But each call is recorded in a global registry with its source location.

### Validate in tests

```python
from symref import validate_refs

def test_all_refs_resolve():
    validate_refs()

def test_celery_task_refs():
    validate_refs(kind="celery_task")
```

If any path can't be resolved, `validate_refs()` raises `SymrefError` with all broken references and their source locations:

```
symref.SymrefError: 2 broken reference(s):
  - "myapp.tasks.send_email" (defined in config/celery.py:8)
  - "myapp.tasks.process_order" (defined in config/celery.py:9)
```

## API

### `ref(path, *, kind=None)`

Creates a forward reference. Returns a `str` subclass instance.

- **`path`** -- fully qualified dotted import path (module or attribute)
- **`kind`** *(optional)* -- arbitrary label for filtering validation (e.g. `"celery_task"`, `"django_app"`)

### `validate_refs(kind=None)`

Checks that every registered ref resolves to a real module or attribute. Raises `SymrefError` if any are broken. Pass `kind` to validate only refs with that label.

### `SymrefError`

Raised when one or more refs can't be resolved. The `.broken` attribute contains the list of broken `ref` instances.

## How it works

- `ref()` is a `str` subclass -- zero overhead after construction
- Each `ref()` call appends to `ref._registry` and captures the caller's file/line via `sys._getframe()`
- `validate_refs()` uses `importlib.util.find_spec()` to check modules, and imports the parent module only when verifying attributes
- No imports happen at `ref()` construction time -- validation is fully deferred

## License

MIT
