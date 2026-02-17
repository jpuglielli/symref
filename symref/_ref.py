from __future__ import annotations

from typing import ClassVar, Self

from symref._source import _capture_source


class ref(str):  # noqa: N801
    __slots__ = ("_kind", "_source")

    _registry: ClassVar[list[ref]] = []
    _kind: str | None
    _source: tuple[str, int]

    def __new__(cls, value: str, *, kind: str | None = None) -> Self:
        instance = super().__new__(cls, value)
        instance._kind = kind
        instance._source = _capture_source()
        cls._registry.append(instance)
        return instance
