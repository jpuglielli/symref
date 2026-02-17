# `symref` — Symbolic Reference Library Spec

## Overview

`symref` is a lightweight Python library for forward-referencing Python objects by their dotted import path, with refactor safety enforced at test/CI time. It has negligible startup overhead and zero per-request overhead.

---

## Motivation

Many Python frameworks accept dotted string paths as configuration:

```python
# Celery
app.conf.task_routes = {
    "webom.part.kafka.consumer.tasks.kafka_consumer_worker": {"queue": "part-kafka"},
}

# Django
INSTALLED_APPS = ["webom.apps.WebomConfig"]

# Celery beat
beat_schedule = {
    "sync-parts": {
        "task": "webom.part.tasks.sync_parts",
    }
}
```

These strings are invisible to refactoring tools, IDEs, and static analyzers. Renaming a module silently breaks them. `symref` solves this by making the reference explicit and validatable, while remaining a plain `str` to any consuming framework.

---

## Goals

- **Refactor safety** — broken paths are caught in tests, not in production
- **Negligible overhead** — one list append per `ref()` call, at import time only
- **Zero per-request overhead** — `ref` instances are plain strings after construction
- **Framework agnostic** — works anywhere a dotted string path is accepted
- **Forward reference support** — does not require the target to be importable at definition time; validation is deferred
- **No new runtime dependencies**

---

## Non-Goals

- Not a replacement for real imports where real imports are possible
- Not a runtime resolver (does not call `importlib.import_module`)
- Not a type-safe proxy to the referenced object
- Not a mypy plugin (though one could be built on top)

---

## API

### `ref(path: str, *, kind: str | None = None) -> str`

Creates a validated forward reference. Returns a `str` subclass instance that is indistinguishable from a plain string to any consumer.

```python
from symref import ref

app.conf.task_routes = {
    ref("webom.part.kafka.consumer.tasks.kafka_consumer_worker"): {"queue": "part-kafka"},
    ref("webom.variant.tasks.variant_assignments_for_config_change"): {"queue": "variant-compute"},
}
```

**Parameters:**

- `path` — fully qualified dotted import path to a module or attribute within a module
- `kind` *(optional)* — an arbitrary label for grouping references (e.g. `"celery_task"`, `"django_app"`). Used to filter validation.

**Behavior:**

- Registers `self` in the global `ref._registry` list at construction time
- Returns an instance that compares equal to the equivalent plain `str`
- Does **not** attempt to import or resolve the path at construction time

---

### `validate_refs(kind: str | None = None) -> None`

Iterates the registry and checks that each path resolves to a real importable location. Raises `SymrefError` if any path is broken.

```python
from symref import validate_refs

validate_refs()          # check all refs
validate_refs("celery_task")  # check only refs with kind="celery_task"
```

**Resolution logic:**

For a path like `"webom.part.kafka.consumer.tasks.kafka_consumer_worker"`:

1. Try `find_spec("webom.part.kafka.consumer.tasks.kafka_consumer_worker")` — succeeds if the path is a module
2. If that fails, split on the last `.` and try `find_spec("webom.part.kafka.consumer.tasks")`, then verify `kafka_consumer_worker` is an attribute of that module
3. If both fail, raise `SymrefError`

Uses `importlib.util.find_spec()` — no side-effecting imports are executed during validation unless attribute checking requires loading the parent module.

---

### `SymrefError`

Raised by `validate_refs()` when one or more paths cannot be resolved. Reports all broken paths in a single raise rather than failing on the first.

```
symref.SymrefError: 2 broken reference(s):
  - "webom.part.kafka.consumer.tasks.kafka_consumer_worker" (defined in config/celery.py:8)
  - "webom.variant.tasks.variant_assignments_for_config_change" (defined in config/celery.py:9)
```

The error message includes the file and line number where each `ref()` was constructed, captured via `inspect.stack()` at construction time.

---

## Internal Design

### `ref` class

```python
class ref(str):
    _registry: list["ref"] = []

    def __new__(cls, value: str, *, kind: str | None = None):
        instance = super().__new__(cls, value)
        instance._kind = kind
        instance._source = _capture_source()  # file + lineno via inspect
        cls._registry.append(instance)
        return instance
```

- Inherits from `str` — no magic `__str__`, no proxying, no overhead after construction
- Registry is a plain list — one append per `ref()` call

### `_capture_source() -> tuple[str, int]`

Uses `inspect.stack()` to walk up to the first frame outside of `symref` itself and record the file path and line number. Called once at construction time.

### `validate_refs()`

```python
def validate_refs(kind: str | None = None) -> None:
    targets = [r for r in ref._registry if kind is None or r._kind == kind]
    broken = []
    for r in targets:
        if not _resolve(r):
            broken.append(r)
    if broken:
        raise SymrefError(broken)
```

---

## Integration Patterns

### pytest

```python
# tests/test_symrefs.py
from symref import validate_refs

def test_all_symrefs_resolve():
    validate_refs()
```

Or with kind filtering:

```python
def test_celery_task_routes():
    validate_refs(kind="celery_task")
```

### Django system check

```python
# apps.py
from django.core.checks import Error, register
from symref import validate_refs, SymrefError

@register()
def check_symrefs(app_configs, **kwargs):
    try:
        validate_refs()
        return []
    except SymrefError as e:
        return [Error(str(e), id="symref.E001")]
```

This surfaces broken references during `manage.py check`, which runs in CI and before `runserver`.

### Celery task routes (primary use case)

```python
from symref import ref

app.conf.task_routes = {
    ref("webom.part.kafka.consumer.tasks.kafka_consumer_worker", kind="celery_task"): {
        "queue": "part-kafka"
    },
    ref("webom.variant.tasks.variant_assignments_for_config_change", kind="celery_task"): {
        "queue": "variant-compute"
    },
}
```

---

## Performance Characteristics

| Operation | When | Cost |
|---|---|---|
| `ref()` construction | Module import (once per process) | `str.__new__` + 1 list append + `inspect.stack()` |
| Framework reads the value | Per use | Identical to reading a plain `str` |
| `validate_refs()` | Test / CI only | `find_spec()` per registered ref |

`inspect.stack()` is the most expensive part of construction. If this becomes a concern (e.g. thousands of refs), source capture can be made opt-in via `ref(..., capture_source=False)`.

---

## File Structure

```
symref/
├── __init__.py          # exports: ref, validate_refs, SymrefError
├── _ref.py              # ref class + registry
├── _validate.py         # validate_refs, _resolve, SymrefError
├── _source.py           # _capture_source via inspect
├── py.typed             # PEP 561 marker
└── tests/
    ├── test_ref.py
    ├── test_validate.py
    └── fixtures/
        └── valid_module.py
```

---

## Open Questions

1. **Should the registry be clearable?** Useful for test isolation if tests register refs themselves. Could expose `ref._registry.clear()` or a context manager.
2. **Thread safety of the registry?** Module imports are effectively single-threaded in CPython due to the import lock, so list appends during import are safe. Explicit `ref()` calls from multiple threads at runtime would not be.
3. **Should `validate_refs()` import the parent module to check attributes, or only use `find_spec()`?** Importing has side effects; `find_spec()` alone can't verify the attribute exists. Could offer both modes.
4. **Mypy/pyright stub?** `ref` returning `str` means type checkers see it as `str`, which is correct. No stubs needed unless we want to type-narrow on `kind`.