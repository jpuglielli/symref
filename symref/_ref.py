from __future__ import annotations

from typing import ClassVar, Self

from symref._source import _capture_source


class ref(str):  # noqa: N801
    """
    A ``str`` subclass that acts as a forward reference to a dotted import path.

    Every ``ref`` instance is registered in a global registry so that all
    references can later be validated in one shot via
    :func:`~symref.validate_refs`.  Because ``ref`` inherits from ``str``,
    frameworks that accept dotted-path strings (Celery, Django, etc.) can
    consume it transparently.
    """

    __slots__ = ("_kind", "_source")

    _registry: ClassVar[list[ref]] = []
    _kind: str | None
    _source: tuple[str, int]

    def __new__(cls, value: str, *, kind: str | None = None) -> Self:
        """
        Create a new forward reference.

        Args:
            value: Fully-qualified dotted import path (e.g.
                ``"myapp.tasks.send_email"``).
            kind: Optional label used to filter validation (e.g.
                ``"celery_task"``).

        """
        instance = super().__new__(cls, value)
        instance._kind = kind
        instance._source = _capture_source()
        cls._registry.append(instance)
        return instance

    def __reduce__(self) -> tuple[type, tuple[str]]:
        """Pickle as a plain ``str`` to avoid re-registering on unpickle."""
        return (str, (str(self),))
