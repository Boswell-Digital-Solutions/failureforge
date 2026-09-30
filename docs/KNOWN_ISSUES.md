# Known Issues

This file tracks open defects, gaps, and their history. Each entry has a date, what is wrong, the root cause, the fix if any, and an explicit open or closed scope. It is not a full defect audit.

## 2026-09-30 Cross-repo integration with DataForge Local, Forge Command and ERA — FF-20260930

**Evidence.** Read-only source review of `failureforge`, `dataforge-Local`, `Forge_Command`, `ERA` and `bds-QRE`, all on branch `claude/failureforge-bad-qre-integration-66koo8`, and one run of `scripts/ci_gate.sh` in a local virtualenv.

### FF-20260930-001 — The DataForge Local server side does not exist (Open)

**What is wrong:** `README.md` and `CLAUDE.md` say DataForge Local owns the operator API under `dataforge-Local/app/failureforge/`. That package does not exist in `dataforge-Local`, and its `app/main.py` mounts no FailureForge router. Every HTTP client in this repository targets routes that no server provides: `persistence/dataforge_client.py`, `promotion/client.py` and `forgecommand/client.py`. The CLI commands `morning-report`, `view-run` and `view-receipt` cannot succeed.

**Test impact (measured 2026-09-30):** slices 04 to 06 and the reconciliation half of slice 10 skip only when FastAPI is absent or the `dataforge-Local` folder is absent. With both present, the tests import `app.failureforge.*` inside test helpers and fail, not skip. `pytest` with the sibling present: `test_dataforge_same_receipt_id_same_hash_is_accepted_successfully` and `test_dataforge_same_receipt_id_different_valid_hash_is_rejected_immutable` fail with `ModuleNotFoundError`. CI does not see this, because the sibling is absent there.

**Root cause:** not determined. The `dataforge-Local` clone is shallow, so an earlier removal is not ruled out. Tracked also in `dataforge-Local/docs/KNOWN_ISSUES.md`.

**Fix:** none. `README.md` now states the gap.

**Scope:** open.

### FF-20260930-002 — The client can change promotion status without an approval receipt (Open)

**What is wrong:** `DataForgeFailureForgeClient.transition_promotion_status` (`persistence/dataforge_client.py:124-132`) posts `{new_status}` to `/receipts/{id}/promotion` with no writer identity. `test_slice_04` calls it the same way. The doctrine says operator approval is mediated by an `ApprovalReceipt` (`POST /approvals`, `X-FailureForge-Writer: operator`). A server built to match this client would open a path around that gate.

**Root cause:** the push-side client (slice 04) predates the approval handshake (slice 06), and the older route was kept.

**Fix:** none. Remove the method, or make the server refuse the route.

**Scope:** open. It becomes a live defect only when DataForge Local implements the route.

### FF-20260930-003 — Two receipt states have no producer (Open)

**What is wrong:** `FailureHarvestReceipt.v1` allows `promoted_to_regression_gate` and `closed_by_fix`. `ApprovalReceipt.v1` cannot set either one, and no other code path sets them. `RootCauseCluster.v1` statuses `closed_by_fix` and `superseded` also have no transition code.

**Root cause:** the states reserve the SMITH and repair outcomes. The actor that records them is not defined.

**Fix:** none.

**Scope:** open. It needs a decision on which authority writes these states.

### FF-20260930-004 — Bridge artifacts have no consumer (Open)

**What is wrong:** `FailureForgeToERAExport.v1`, `FailureForgeAARSeed.v1`, `RootCauseCluster.v1`, `FixClusterReport.v1` and the adjudication reports are written locally or built in memory. No route pushes them to DataForge Local. ERA does not read `FailureForgeToERAExport.v1`: ERA's intake reads only its own evaluation exports. Forge Command therefore always shows empty cluster and adjudication sections (`Forge_Command/docs/KNOWN_ISSUES.md`, FC-FFQ-20260930-006).

**Root cause:** the bridge contracts are drafts (`x-contract-governance.promotion_status: draft`). The consumer side was not built.

**Fix:** none.

**Scope:** open. A path must be chosen: a DataForge Local route, Forge Command's Centipede inbox (`~/.forge-command/centipede-inbox/`), or ERA intake.

### FF-20260930-005 — No link to bds-QRE (Observation)

No plan connects FailureForge to the Quality-Ratchet Evaluator (`bds-QRE`). FailureForge severities equal QRE issue severities, and clusters carry stable fingerprints, so a collector could map receipts to QRE observations. QRE accepts evidence only from authorized, non-simulated collectors, and no checkpoint of `BDS-QRE-MODULE-v0.1` names FailureForge. Any such collector needs its own authorization.

### FF-20260930-006 — A slice-10 test reads a moved file, so the local gate fails on `master` (Open)

**What is wrong:** `test_governance_docs_state_failureforge_role` (`tests/test_slice_10_governance_reconciliation.py:169`) reads `doc/system/00_overview/00-purpose.md`. That file is now `doc/system/00-purpose.md`. The test fails with `FileNotFoundError`, and `scripts/ci_gate.sh` stops at its `pytest` step. Reproduced on `master` at `7250980`.

**Root cause:** PR #4 (`5cec91d`) flattened `doc/system/` and did not update the test path.

**Fix:** PR #7 changes the path to `doc/system/00-purpose.md`. The asserted sentences are still at `doc/system/00-purpose.md:9`. The local gate passes on that branch.

**Scope:** open.

### FF-20260930-007 — GitHub Actions jobs get no runner (Open)

**What is wrong:** every CI Gate run since 2026-09-25 (runs 10 to 15) ends in 2 to 8 seconds with conclusion `failure`, `runner_id: 0` and no runner name. No log exists. No step runs, not even checkout. This covers #4, its push to `master`, #5, #6 and #7. A re-run of #7 on 2026-09-30 failed the same way. The last successful run (2026-09-09) took about 20 seconds.

**Root cause:** not determined from the API. A job that never gets a runner usually means Actions is blocked at the account or repository level, for example a spending limit or a billing problem. The run annotation names the cause.

**Consequence:** a red CI Gate check in this period says nothing about the code. FF-20260930-006 was found by a local run, not by CI.

**Fix:** none from the repository. Check the Actions billing and settings for the account.

**Scope:** open.
