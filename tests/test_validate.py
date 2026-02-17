from __future__ import annotations

import pytest

from symref import SymrefError, ref, validate_refs
from symref._validate import _resolve


def setup_function() -> None:
    ref._registry.clear()


# --- _resolve tests ---


def test_resolve_valid_module() -> None:
    assert _resolve("os") is True


def test_resolve_valid_nested_module() -> None:
    assert _resolve("os.path") is True


def test_resolve_valid_attribute() -> None:
    assert _resolve("os.path.join") is True


def test_resolve_valid_package_module() -> None:
    assert _resolve("symref._ref") is True


def test_resolve_valid_package_attribute() -> None:
    assert _resolve("symref._ref.ref") is True


def test_resolve_valid_package_class_var() -> None:
    assert _resolve("symref.SymrefError") is True


def test_resolve_nonexistent_module() -> None:
    assert _resolve("nonexistent.module.that.does.not.exist") is False


def test_resolve_nonexistent_attribute() -> None:
    assert _resolve("os.path.nonexistent_attr_xyz") is False


def test_resolve_relative_path() -> None:
    assert _resolve(".foo.bar") is False


def test_resolve_double_relative_path() -> None:
    assert _resolve("..foo") is False


def test_resolve_whitespace_path() -> None:
    assert _resolve("  ") is False


def test_resolve_empty_string() -> None:
    assert _resolve("") is False


# --- validate_refs tests ---


def test_validate_no_refs_passes() -> None:
    validate_refs()


def test_validate_valid_ref_passes() -> None:
    ref("os.path")
    validate_refs()


def test_validate_broken_ref_raises() -> None:
    ref("nonexistent.module.xyz")
    with pytest.raises(SymrefError):
        validate_refs()


def test_validate_multiple_broken_refs() -> None:
    ref("nonexistent.module.one")
    ref("nonexistent.module.two")
    with pytest.raises(SymrefError, match="2 broken reference"):
        validate_refs()


def test_validate_kind_filtering_passes() -> None:
    ref("os.path", kind="good")
    ref("nonexistent.module.xyz", kind="bad")
    validate_refs(kind="good")


def test_validate_kind_filtering_raises() -> None:
    ref("os.path", kind="good")
    ref("nonexistent.module.xyz", kind="bad")
    with pytest.raises(SymrefError):
        validate_refs(kind="bad")


def test_error_message_includes_source() -> None:
    ref("nonexistent.module.xyz")
    with pytest.raises(SymrefError, match=r"test_validate\.py"):
        validate_refs()


def test_validate_valid_attribute_ref() -> None:
    ref("symref.SymrefError")
    validate_refs()


def test_validate_invalid_attribute_ref() -> None:
    ref("symref.NonexistentThing")
    with pytest.raises(SymrefError):
        validate_refs()


def test_validate_mixed_valid_and_broken_refs() -> None:
    ref("os.path")
    ref("nonexistent.module.xyz")
    ref("os")
    with pytest.raises(SymrefError) as exc_info:
        validate_refs()
    assert len(exc_info.value.broken) == 1
    assert str(exc_info.value.broken[0]) == "nonexistent.module.xyz"


def test_symref_error_broken_attribute() -> None:
    r = ref("nonexistent.module.xyz")
    with pytest.raises(SymrefError) as exc_info:
        validate_refs()
    assert exc_info.value.broken == [r]
    assert exc_info.value.broken[0] is r
