"""Slice 26: FailureForge produces evidence and never submits a decision.

DataForge Local's DFL-FFG-02 routes accept an approval or a promotion
candidate only with a token that Forge_Command signed for that one decision.
The writer header is logged and never trusted (ruling R3), and FailureForge is
the content producer, not a signer or submitter (ruling R8). The old
``X-FailureForge-Writer`` / ``X-FailureForge-Token`` clients, the ungated
status route, and the withdraw and SMITH routes they called are gone.

The first test runs everywhere. The cross-repo tests need the sibling
``dataforge-Local`` checkout and skip without it, like slices 04 to 05.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

import pytest

_FF_ROOT = Path(__file__).resolve().parents[1]
_DATAFORGE_LOCAL = _FF_ROOT.parent / "dataforge-Local"

_DECISION_ROUTE = re.compile(
    r"/approvals|/promotion-candidates|/promotion\b|smith-pickup|smith-decision|/withdraw"
)
_RETIRED_HEADERS = ("X-FailureForge-Writer", "X-FailureForge-Token")


def test_failureforge_source_never_submits_a_decision():
    offenders = []
    for path in sorted((_FF_ROOT / "src" / "failureforge").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            if _DECISION_ROUTE.search(line) or any(h in line for h in _RETIRED_HEADERS):
                offenders.append(
                    f"{path.relative_to(_FF_ROOT)}:{lineno}: {line.strip()}"
                )
    assert offenders == []


def _dataforge_app():
    pytest.importorskip(
        "fastapi", reason="dataforge-Local integration test requires fastapi"
    )
    pytest.importorskip(
        "cryptography", reason="the decision-token check needs cryptography"
    )
    if not _DATAFORGE_LOCAL.exists():
        pytest.skip(
            "dataforge-Local sibling repo not present; cross-repo integration test"
        )
    if str(_DATAFORGE_LOCAL) not in sys.path:
        sys.path.insert(0, str(_DATAFORGE_LOCAL))

    from app.failureforge.router import router
    from app.failureforge.service import FailureForgeService
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from execution_authority.services.failureforge_operator_token import (
        FailureForgeOperatorVerifier,
    )
    from execution_authority.services.run_token import PUBLIC_KEYS_ENV
    from fastapi import FastAPI

    raw = (
        Ed25519PrivateKey.generate()
        .public_key()
        .public_bytes(Encoding.Raw, PublicFormat.Raw)
    )
    key = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    app = FastAPI()
    app.include_router(router)
    app.state.failureforge_service = FailureForgeService()
    app.state.failureforge_operator_verifier = FailureForgeOperatorVerifier.from_env(
        {PUBLIC_KEYS_ENV: json.dumps({"slice-26-kid": key})}
    )
    return app


@pytest.fixture
def seeded(tmp_path: Path):
    app = _dataforge_app()
    from fastapi.testclient import TestClient

    from failureforge.persistence import DataForgeFailureForgeClient
    from failureforge.runtime.sandbox import SandboxRunner

    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    SandboxRunner(
        sandbox_root=sandbox,
        target_repo_name="example-repo",
        target_repo_source=_FF_ROOT / "sandbox-targets" / "example-repo",
    ).run(sandbox_run_id="SR-authority")
    http = TestClient(app)
    summary = DataForgeFailureForgeClient(http_client=http).push_run_bundle_from_disk(
        run_id="SR-authority", sandbox_root=sandbox
    )
    assert summary.all_accepted
    receipt_id = app.state.failureforge_service.list_receipts(
        sandbox_run_id="SR-authority"
    )[0]["receipt_id"]
    return http, app.state.failureforge_service, receipt_id


def _assert_undecided(http, receipt_id: str) -> None:
    """The current status column is unchanged and no decision is recorded."""
    state = http.get(
        f"/api/v1/failureforge/operator/receipts/{receipt_id}/approvals"
    ).json()
    assert state["promotion_status"] == "pending_operator_review"
    assert state["approval_head"] is None
    assert state["approvals"] == []
    candidates = http.get(
        f"/api/v1/failureforge/operator/receipts/{receipt_id}/candidates"
    )
    assert candidates.status_code == 200


def _old_model_approval(receipt_id: str) -> dict:
    return {
        "approval_receipt": {
            "schema_version": "ApprovalReceipt.v1",
            "approval_receipt_id": "AR-slice26",
            "failure_receipt_id": receipt_id,
            "decided_by": "operator:demo",
            "decided_at": "2026-10-13T00:00:00.000000Z",
            "decision": "approved_for_smith_review",
            "prior_promotion_status": "pending_operator_review",
            "new_promotion_status": "approved_for_smith_review",
        },
        "expected_approval_head": None,
    }


@pytest.mark.parametrize(
    "headers",
    [
        {"X-FailureForge-Writer": "operator", "X-FailureForge-Token": "local-operator"},
        {"X-FailureForge-Writer": "operator", "Authorization": "Bearer local-operator"},
    ],
    ids=["retired-writer-headers", "unsigned-bearer"],
)
def test_approval_without_a_forge_command_token_is_refused(seeded, headers):
    http, _service, receipt_id = seeded
    response = http.post(
        "/api/v1/failureforge/approvals",
        json=_old_model_approval(receipt_id),
        headers=headers,
    )
    assert response.status_code == 401, response.text
    _assert_undecided(http, receipt_id)


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/failureforge/receipts/{receipt_id}/promotion",
        "/api/v1/failureforge/promotion-candidates/PC-any/withdraw",
        "/api/v1/failureforge/promotion-candidates/PC-any/smith-pickup",
        "/api/v1/failureforge/promotion-candidates/PC-any/smith-decision",
    ],
)
def test_retired_routes_do_not_exist(seeded, path):
    http, _service, receipt_id = seeded
    response = http.post(path.format(receipt_id=receipt_id), json={})
    assert response.status_code in (404, 405)
    _assert_undecided(http, receipt_id)
