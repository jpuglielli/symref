from symref._ref import ref
from symref._validate import SymrefError, validate_refs


def clear_refs() -> None:
    """
    Clear the global ref registry.

    Useful for test isolation when tests register their own refs.
    """
    ref._registry.clear()


__all__ = ["SymrefError", "clear_refs", "ref", "validate_refs"]
