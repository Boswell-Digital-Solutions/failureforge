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

## Review qualifications — not additional confirmed defects

At the source lock above, `doc/system/20-contracts.md` describes the Slice 10 ERA/AAR bridge contracts and `TargetAdapter.v1` as locally owned drafts, with intended future shared-contract authority. A bridge implementation alone is not evidence of shared-contract admission. Current `forge_contract_core` admission was not reverified for this recording task, so this log neither asserts admission nor declares its absence. Reconcile admission and consumer evidence before making an ecosystem-wide interoperability claim; do not promote or alter contracts through this log.

## Recording authority

The operator requested known-issues documentation on 2026-09-30. This change records findings only. It changes no runtime, build script, generated reference, contract, CI enforcement, baseline, approval, or deployment, and marks no finding fixed.
