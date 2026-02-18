from __future__ import annotations

from symref import ref


def test_ref_is_str() -> None:
    r = ref("os.path")
    assert isinstance(r, str)


def test_ref_equals_plain_str() -> None:
    r = ref("os.path")
    assert r == "os.path"
    assert "os.path" == r  # noqa: SIM300 -- intentionally testing str.__eq__(ref)


def test_ref_registered_in_registry() -> None:
    r = ref("os.path")
    assert r in ref._registry
    assert len(ref._registry) == 1


def test_kind_defaults_to_none() -> None:
    r = ref("os.path")
    assert r._kind is None


def test_kind_stored_when_provided() -> None:
    r = ref("os.path", kind="test_kind")
    assert r._kind == "test_kind"


def test_source_captured() -> None:
    r = ref("os.path")
    assert r._source[0].endswith("test_ref.py")
    assert isinstance(r._source[1], int)
    assert r._source[1] > 0


def test_usable_as_dict_key() -> None:
    r = ref("os.path")
    d: dict[str, str] = {r: "value"}
    assert d["os.path"] == "value"
    assert d[r] == "value"


def test_repr_matches_str() -> None:
    r = ref("os.path")
    assert repr(r) == repr("os.path")


def test_hash_matches_str() -> None:
    r = ref("os.path")
    assert hash(r) == hash("os.path")


def test_registry_clearing() -> None:
    ref("os.path")
    assert len(ref._registry) == 1
    ref._registry.clear()
    assert len(ref._registry) == 0
