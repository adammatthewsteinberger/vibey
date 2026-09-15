"""Tests for ``vibey_bootstrap.ingress``."""

from __future__ import annotations

import io
import zipfile

import pytest

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import OversizedAttachmentError, ZipBombError
from vibey_bootstrap.ingress import (
    AttachmentClassifier,
    ExtensionAllowlist,
    MimeAllowlist,
    classify_bytes,
    enforce_size_cap,
    enforce_zip_safety_limits,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()


class TestExtensionAllowlist:
    def test_case_insensitive(self) -> None:
        a = ExtensionAllowlist({".pdf"})
        assert a.allows("Report.PDF") is True
        assert a.allows("report.pdf") is True

    def test_reject_reason(self) -> None:
        a = ExtensionAllowlist({".pdf"})
        assert a.reject_reason("report.exe") == "unsupported_extension: .exe"
        assert a.reject_reason("report.pdf") is None

    def test_normalizes_dotless_input(self) -> None:
        a = ExtensionAllowlist({"pdf", "zip"})  # no leading dots
        assert a.allows("x.pdf") is True


class TestMimeAllowlist:
    def test_accepts_octet_stream(self) -> None:
        m = MimeAllowlist()
        assert m.allows("application/octet-stream") is True

    def test_rejects_unknown(self) -> None:
        m = MimeAllowlist()
        assert m.allows("application/x-msdownload") is False
        assert m.reject_reason("application/x-msdownload") is not None

    def test_strips_charset(self) -> None:
        m = MimeAllowlist()
        assert m.allows("application/pdf; charset=utf-8") is True


class TestClassifyBytes:
    def test_pdf(self) -> None:
        assert classify_bytes(b"%PDF-1.7\nxxx") == "pdf"

    def test_zip(self) -> None:
        assert classify_bytes(b"PK\x03\x04rest") == "zip"

    def test_gzip_rejected_when_not_allowed(self) -> None:
        assert classify_bytes(b"\x1f\x8b...", allowed=("pdf", "zip")) == "reject"

    def test_png_rejected_when_not_allowed(self) -> None:
        assert classify_bytes(b"\x89PNG\r\n\x1a\n", allowed=("pdf", "zip")) == "reject"

    def test_unknown_rejected(self) -> None:
        assert classify_bytes(b"abc") == "reject"

    def test_non_bytes_rejected(self) -> None:
        assert classify_bytes("not bytes") == "reject"  # type: ignore[arg-type]


class TestSizeCap:
    def test_raises_oversized(self) -> None:
        with pytest.raises(OversizedAttachmentError):
            enforce_size_cap(size_bytes=200_000_000, cap_bytes=150_000_000, filename="x.pdf")

    def test_under_cap_passes(self) -> None:
        enforce_size_cap(size_bytes=100, cap_bytes=200, filename="x.pdf")

    def test_bumps_counter(self) -> None:
        with pytest.raises(OversizedAttachmentError):
            enforce_size_cap(
                size_bytes=200,
                cap_bytes=100,
                filename="x.pdf",
                counter_name="attachment.rejected.size_cap",
            )
        assert counter_snapshot().get("attachment.rejected.size_cap", 0) == 1


class TestZipSafety:
    def _zip_with_entries(self, n: int) -> zipfile.ZipFile:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(n):
                zf.writestr(f"f{i}.txt", "x")
        buf.seek(0)
        return zipfile.ZipFile(buf, "r")

    def test_rejects_excessive_entries(self) -> None:
        zf = self._zip_with_entries(15)
        with pytest.raises(ZipBombError):
            enforce_zip_safety_limits(zf, filename="big.zip", max_entries=10)

    def test_rejects_excessive_uncompressed_size(self) -> None:
        zf = self._zip_with_entries(3)
        # max_entries large enough; pin uncompressed cap below the actual size.
        with pytest.raises(ZipBombError):
            enforce_zip_safety_limits(
                zf,
                filename="x.zip",
                max_entries=100,
                max_uncompressed_bytes=1,
            )

    def test_under_limits_passes(self) -> None:
        zf = self._zip_with_entries(3)
        enforce_zip_safety_limits(zf, filename="x.zip")


class TestClassifierPipeline:
    def test_pipeline_order_extension_rejects_first(self) -> None:
        """Pass an .exe with PDF MIME + PDF magic bytes — extension must reject first."""
        c = AttachmentClassifier()
        result = c.classify(
            filename="report.exe",
            content_type="application/pdf",
            size_bytes=10,
            content=b"%PDF-1.7",
        )
        assert result.allowed is False
        assert "unsupported_extension" in (result.reject_reason or "")
        assert counter_snapshot().get("attachment.rejected.unsupported_type", 0) == 1

    def test_mime_rejects_when_extension_passes(self) -> None:
        c = AttachmentClassifier()
        result = c.classify(
            filename="report.pdf",
            content_type="application/x-msdownload",
            size_bytes=10,
            content=b"%PDF-1.7",
        )
        assert result.allowed is False
        assert "mime" in (result.reject_reason or "")

    def test_magic_byte_rejects_when_others_pass(self) -> None:
        c = AttachmentClassifier()
        result = c.classify(
            filename="report.pdf",
            content_type="application/pdf",
            size_bytes=10,
            content=b"NOPE",
        )
        assert result.allowed is False
        assert "magic_byte" in (result.reject_reason or "")

    def test_extension_mismatch_flag(self) -> None:
        """Real PDF named .zip — bytes are authoritative; pass through with flag."""
        c = AttachmentClassifier()
        result = c.classify(
            filename="report.zip",
            content_type="application/octet-stream",
            size_bytes=10,
            content=b"%PDF-1.7",
        )
        assert result.allowed is True
        assert result.kind == "pdf"
        assert result.extension_mismatch is True
        assert counter_snapshot().get("attachment.mismatched_extension", 0) == 1

    def test_size_cap_applied_per_kind(self) -> None:
        c = AttachmentClassifier(size_caps={"pdf": 5})
        result = c.classify(
            filename="report.pdf",
            content_type="application/pdf",
            size_bytes=100,
            content=b"%PDF-1.7" + b"x" * 1000,
        )
        assert result.allowed is False
        assert "size_cap" in (result.reject_reason or "")
