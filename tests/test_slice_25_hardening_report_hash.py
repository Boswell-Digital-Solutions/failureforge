"""Slice 25: the hardening report carries a committed hash (report_hash).

The hash is optional in the schema, so reports written before this slice stay valid.
Every report that ``build_hardening_report`` writes now carries one. The hash is
defined like ``receipt_hash``: a SHA-256 over every other field.
"""

from __future__ import annotations

import copy

import pytest

from failureforge.reporting.scorer import build_hardening_report
from failureforge.validation import (
    ReportHashMismatch,
    SchemaValidationError,
    apply_receipt_hash,
    apply_report_hash,
    compute_report_hash,
    validate_hardening_report,
    verify_report_hash,
)


def _receipt(n: int = 1, *, severity: str = "high") -> dict:
    return apply_receipt_hash(
        {
            "schema_version": "FailureHarvestReceipt.v1",
            "receipt_id": f"FHR-{n:04d}",
            "failure_case_id": "FC-edge-1",
            "sandbox_run_id": "SR-demo",
            "target_repo": "example-repo",
            "target_ref": "main",
            "classification": "timeout",
            "severity": severity,
            "expected_result": "pass",
            "actual_result": "fail",
            "reproducible": True,
            "repro_command": "pytest -k slow",
            "artifact_paths": ["out/a.log"],
            "promotion_status": "pending_operator_review",
            "created_at": "2026-09-30T12:00:00Z",
        }
    )


def _report() -> dict:
    return build_hardening_report(
        sandbox_run_id="SR-demo",
        target_repo="example-repo",
        receipts=[_receipt(1), _receipt(2, severity="low")],
    )


def test_a_built_report_carries_a_valid_hash():
    report = _report()
    assert len(report["report_hash"]) == 64
    verify_report_hash(report)
    validate_hardening_report(report)


def test_changing_any_field_breaks_the_hash():
    report = _report()
    tampered = copy.deepcopy(report)
    tampered["ranked_findings"][0]["severity"] = "info"
    with pytest.raises(ReportHashMismatch):
        verify_report_hash(tampered)
    # A changed float is also detected.
    tampered = copy.deepcopy(report)
    tampered["ranked_findings"][0]["score"] += 0.5
    with pytest.raises(ReportHashMismatch):
        verify_report_hash(tampered)


def test_the_hash_ignores_key_order_and_its_own_field():
    report = _report()
    reordered = dict(reversed(list(report.items())))
    assert compute_report_hash(reordered) == report["report_hash"]
    without = {k: v for k, v in report.items() if k != "report_hash"}
    assert compute_report_hash(without) == report["report_hash"]
    assert apply_report_hash(without)["report_hash"] == report["report_hash"]


def test_a_report_without_a_hash_is_still_valid_but_does_not_verify():
    report = _report()
    legacy = {k: v for k, v in report.items() if k != "report_hash"}
    validate_hardening_report(legacy)
    with pytest.raises(ReportHashMismatch, match="no report_hash"):
        verify_report_hash(legacy)


@pytest.mark.parametrize("bad", ["", "abc123", "A" * 64, "g" * 64, "a" * 63, "a" * 65])
def test_the_schema_rejects_a_malformed_hash(bad: str):
    report = _report()
    report["report_hash"] = bad
    with pytest.raises(SchemaValidationError):
        validate_hardening_report(report)


def test_the_hash_is_reproducible_for_the_same_inputs_apart_from_the_timestamp():
    a, b = _report(), _report()
    for report in (a, b):
        report.pop("report_hash")
        report["created_at"] = "2026-09-30T12:00:00Z"
    assert compute_report_hash(a) == compute_report_hash(b)


def test_a_pinned_vector_with_floats_and_non_ascii_text():
    """Pins the exact hash of a fixed report. A port to another language must match it.

    The report holds floats. Python writes a float with its shortest round-trip text,
    and the hash depends on that text. Another language must write the same text.
    """
    report = {
        "schema_version": "HardeningReport.v1",
        "report_id": "HR-vector",
        "sandbox_run_id": "SR-vector",
        "target_repo": "example-repo",
        "summary": 'héllo 日本 "quoted" \\ back',
        "ranked_findings": [
            {"rank": 1, "score": 0.30000000000000004, "failure_id": "a"},
            {"rank": 2, "score": 100.0, "failure_id": "b"},
            {"rank": 3, "score": 1e-07, "failure_id": "c"},
        ],
        "created_at": "2026-09-30T12:00:00Z",
        "receipts_total": 3,
        "reproducible_total": 2,
    }
    assert (
        compute_report_hash(report)
        == "8e286933cf65fcaf3ea97c9278f00d5668030d4fff139cda5b47ccd70227d8f4"
    )
