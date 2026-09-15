"""Tests for ``vibey_bootstrap.pdf_safety``."""

from __future__ import annotations

import pytest

from vibey_bootstrap.counters import _reset_counters, counter_snapshot

# pypdf names internal dictionary nodes via these helpers; we avoid full PDF
# construction by using simple dict-like objects that quack like pypdf objects.


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()


class _FakeAnnot:
    def __init__(self, data: dict) -> None:
        self._data = data

    def get_object(self) -> dict:
        return self._data

    # Make the dict ops pass-through for callers that don't get_object():
    def __contains__(self, k: str) -> bool:
        return k in self._data

    def __delitem__(self, k: str) -> None:
        del self._data[k]


class _FakePage(dict):
    pass


class _FakeReader:
    def __init__(self, catalog: dict, pages: list[_FakePage]) -> None:
        self.trailer = {"/Root": catalog}
        self.pages = pages


def test_strips_catalog_open_action() -> None:
    from vibey_bootstrap.pdf_safety import sanitize_pdf_for_passthrough

    catalog = {"/OpenAction": "[malicious]", "/Type": "/Catalog"}
    reader = _FakeReader(catalog, pages=[])
    sanitize_pdf_for_passthrough(reader)
    assert "/OpenAction" not in catalog
    assert "/Type" in catalog  # benign keys preserved
    assert counter_snapshot().get("pdf.sanitized.actions_stripped", 0) == 1


def test_strips_javascript_and_names_tree() -> None:
    from vibey_bootstrap.pdf_safety import sanitize_pdf_for_passthrough

    catalog = {"/JavaScript": "...", "/Names": {"/EmbeddedFiles": "..."}}
    reader = _FakeReader(catalog, pages=[])
    sanitize_pdf_for_passthrough(reader)
    assert "/JavaScript" not in catalog
    assert "/Names" not in catalog


def test_strips_per_page_aa() -> None:
    from vibey_bootstrap.pdf_safety import sanitize_pdf_for_passthrough

    page = _FakePage()
    page["/AA"] = "..."
    page["/Contents"] = "safe"
    reader = _FakeReader({}, pages=[page])
    sanitize_pdf_for_passthrough(reader)
    assert "/AA" not in page
    assert "/Contents" in page


def test_strips_per_annotation() -> None:
    from vibey_bootstrap.pdf_safety import sanitize_pdf_for_passthrough

    annot_data = {"/A": "...", "/AA": "...", "/Subtype": "/Link"}
    page = _FakePage()
    page["/Annots"] = [_FakeAnnot(annot_data)]
    reader = _FakeReader({}, pages=[page])
    sanitize_pdf_for_passthrough(reader)
    assert "/A" not in annot_data
    assert "/AA" not in annot_data
    assert "/Subtype" in annot_data


def test_passes_through_on_exception() -> None:
    from vibey_bootstrap.pdf_safety import sanitize_pdf_for_passthrough

    class BadReader:
        @property
        def trailer(self) -> dict:
            raise RuntimeError("malformed")

        @property
        def pages(self) -> list:
            raise RuntimeError("malformed")

    reader = BadReader()
    result = sanitize_pdf_for_passthrough(reader)
    # Must return the original reader unchanged
    assert result is reader
    # Counter must NOT have been bumped
    assert counter_snapshot().get("pdf.sanitized.actions_stripped") is None


def test_counter_not_bumped_when_no_op() -> None:
    """A clean PDF (no actions to strip) MUST NOT bump the counter."""
    from vibey_bootstrap.pdf_safety import sanitize_pdf_for_passthrough

    catalog = {"/Type": "/Catalog"}
    reader = _FakeReader(catalog, pages=[_FakePage()])
    sanitize_pdf_for_passthrough(reader)
    assert counter_snapshot().get("pdf.sanitized.actions_stripped") is None
