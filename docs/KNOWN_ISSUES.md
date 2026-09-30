# FailureForge Known Issues

Dated findings with source locks, evidence limits, proposed repair scope, and explicit closure criteria. Recording a finding is not authorization to repair, broaden execution, admit a contract, or promote evidence. Existing runtime and human-approval boundaries remain unchanged.

## 2026-09-30 — KI-FFG-20260930-001: Documentation builder ignores --check and rewrites the compiled reference

**Status: OPEN — confirmed by source inspection; repair not applied.**

**Source lock.** `Boswell-Digital-Solutions/failureforge@72509803dd94b093bf481434a6d662f42f5fbabd` (`master`, rechecked 2026-09-30).

**Evidence.** Complete reads of `doc/system/BUILD.sh` and `doc/system/validate_snapshots.sh`. The builder never parses positional arguments. After temporary assembly and marker validation, it unconditionally executes `cp "$TMP_OUTPUT" "$ROOT_DIR/$OUTPUT"` and `chmod 664 "$ROOT_DIR/$OUTPUT"`, then reports `BUILD_OK`. The validator checks required markers, not equality with the committed reference.

**Problem and impact.** `bash doc/system/BUILD.sh --check` follows the normal write path. With valid structure and markers, stale `doc/FFGSYSTEM.md` content can be overwritten instead of producing a parity failure. A successful invocation cannot establish that the committed reference was already current. The inspected FailureForge documentation prescribes assembly; this is a missing check mode, not evidence of QRE's specific documented `BUILD_STALE` contradiction in this repository.

**Root cause.** No argument dispatch, non-mutating comparison, or stale/missing-output failure path exists. Structural marker validation is not parity validation.

**Verification limits.** No builder or test suite was executed during this review. Current compiled-document staleness, an active CI caller using `--check`, and runtime/deployment status were not established. The defect is confirmed by script inspection, not by a claimed live reproduction.

**Bounded repair proposal — not authorization.** Implement explicit build/check modes. Check mode must assemble and validate in temporary storage, compare against the existing output, and fail on missing or different output without creating, replacing, chmodding, or otherwise modifying repository files. Reject unsupported arguments before side effects. Keep explicit normal assembly available. Do not change probing, replay, receipt, adapter, promotion, or approval behavior.

**Closure evidence required.** At an immutable repair head, prove that: current output passes without byte or mode changes; stale output fails and remains untouched; missing output fails without creation; invalid source/validation failures preserve the output; unsupported arguments fail without writes; and normal build still regenerates the reference. Use an isolated test checkout and record repository state before and after check mode.

**Related findings.** `ERA: KI-ERA-20260930-001`; `bds-QRE: KI-QRE-20260930-001`. Closure is repository-specific.

## 2026-09-30 — KI-FFG-20260930-002: Canonical runtime-boundary chapter omits the documented execution-isolation limits

**Status: OPEN — documentation gap confirmed; no runtime repair performed.**

**Source lock.** `Boswell-Digital-Solutions/failureforge@72509803dd94b093bf481434a6d662f42f5fbabd`.

**Evidence.** `doc/system/_index.md` identifies the source tree as canonical. `doc/system/30-runtime-boundary.md` contains a placeholder directing readers to executable repository truth, but no substantive execution-boundary description. `doc/system/10-current-architecture.md` describes copied workspaces and canonical-source hash checks. The README's "Execution isolation" section and `CLAUDE.md` explicitly explain the limitation absent from the canonical runtime chapter: a filesystem copy is not OS isolation, the target's `registry.py` runs in-process with runner privileges, and source hashes are detective rather than preventive controls.

**Problem and impact.** A reader relying on the canonical runtime chapter does not receive the documented distinction between copy-only probing and an enforced security boundary. They could mistake source-mutation detection for prevention of network access, writes elsewhere, or subprocess side effects. A passing receipt or replay check does not establish containment of arbitrary target code.

**Verification limits.** The documentation omission and README/CLAUDE warning were inspected. No adversarial target was executed, no escape was reproduced, and no current production exposure is asserted. Runtime behavior must be re-read from the implementation before authoring a definitive replacement chapter.

**Bounded documentation repair proposal — not authorization.** Reconcile the runtime chapter with `src/failureforge/runtime/sandbox.py`, replay code, target-adapter behavior, and the existing isolation warning. State the execution context and privileges, permitted write locations, limits of source fingerprinting, the absence of an OS isolation guarantee, and the existing prerequisite for real isolation before non-demo or untrusted execution. Rebuild the compiled reference intentionally and verify parity with a genuine non-mutating check or an independently recorded comparison until KI-FFG-20260930-001 is repaired. Do not imply that documentation adds containment.

**Closure evidence required.** A source-linked, reviewed runtime chapter and matching compiled reference that explicitly preserve the copy-versus-isolation distinction and detective-versus-preventive distinction. Any actual containment implementation, security testing of untrusted targets, or expansion to new targets requires a separately scoped authorization and its own proof; it is not bundled into this documentation issue.

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

## Review qualifications — not additional confirmed defects

At the source lock above, `doc/system/20-contracts.md` describes the Slice 10 ERA/AAR bridge contracts and `TargetAdapter.v1` as locally owned drafts, with intended future shared-contract authority. A bridge implementation alone is not evidence of shared-contract admission. Current `forge_contract_core` admission was not reverified for this recording task, so this log neither asserts admission nor declares its absence. Reconcile admission and consumer evidence before making an ecosystem-wide interoperability claim; do not promote or alter contracts through this log.

## Recording authority

The operator requested known-issues documentation on 2026-09-30. This change records findings only. It changes no runtime, build script, generated reference, contract, CI enforcement, baseline, approval, or deployment, and marks no finding fixed.
