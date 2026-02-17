from __future__ import annotations

import importlib
import importlib.util

from symref._ref import ref


class SymrefError(Exception):
    def __init__(self, broken: list[ref]) -> None:
        self.broken = broken
        lines = [
            f"{len(broken)} broken reference(s):",
            *[f'  - "{r}" (defined in {r._source[0]}:{r._source[1]})' for r in broken],
        ]
        super().__init__("\n".join(lines))


def _resolve(path: str) -> bool:
    if not path:
        return False

    # 1. Try as a full module path
    try:
        spec = importlib.util.find_spec(path)
    except (ImportError, ValueError):
        spec = None

    if spec is not None:
        return True

    # 2. Split on last dot — try parent as module, last part as attribute
    if "." not in path:
        return False

    parent, _, attr = path.rpartition(".")
    try:
        parent_spec = importlib.util.find_spec(parent)
    except (ImportError, ValueError):
        parent_spec = None

    if parent_spec is None:
        return False

    module = importlib.import_module(parent)
    return hasattr(module, attr)


def validate_refs(kind: str | None = None) -> None:
    targets = [r for r in ref._registry if kind is None or r._kind == kind]
    broken = [r for r in targets if not _resolve(r)]
    if broken:
        raise SymrefError(broken)
