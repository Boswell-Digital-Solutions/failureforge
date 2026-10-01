# 20 Contracts

FailureForge keeps its local schemas under `schemas/`.

Current local contracts include:

- `FailureCase.v1`
- `FailureHarvestReceipt.v1`
- `SandboxRun.v1`
- `HardeningReport.v1`
- `ApprovalReceipt.v1`
- `PromotionCandidate.v1`
- `RootCauseCluster.v1`
- `FixClusterReport.v1`
- `ModelAdjudicationReceipt.v1`
- `NeuroForgeAdjudicationReport.v1`
- `FailureScore.v2`
- `FailureForgeToERAExport.v1`
- `FailureForgeAARSeed.v1`
- `TargetAdapter.v1`

Slice 10 bridge contracts are draft contracts owned locally by FailureForge
with intended future authority in `forge-contract-core`. They are read-only
artifacts and carry no mutation, repair, or approval authority.

`TargetAdapter.v1` is also a draft local contract. It must declare supported
attack families, copy strategy, forbidden paths, artifact capture roots, and a
canonical mutation guard before FailureForge expands to a new target.

`SandboxRun.v1` runner-produced records include canonical source hashes before
and after execution plus a mutation flag. Minimal historical run records remain
valid for compatibility.

## Report hash

`HardeningReport.v1` has an optional `report_hash`. It is the SHA-256 of every other
field, written like `receipt_hash`: `json.dumps(report without report_hash,
sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.

- `build_hardening_report` always sets it. A report written before this field stays valid.
- `compute_report_hash`, `apply_report_hash` and `verify_report_hash` are in
  `failureforge.validation`.
- The schema allows a ranked finding `score` to be any number. The scorer today adds
  integer weights, so it always writes an integer (checked 2026-09-30: every weight is
  an `int`, and a real run gave scores such as 96 and 33). A report with a float
  `score` is valid. Python writes a float with its shortest round-trip text, for
  example `1e-07` and `100.0`, and the hash depends on that text. A program in another
  language can recompute the hash for every report the scorer writes today. It cannot
  do so for a float until it matches Python's float text.
- The hash lets a consumer bind a report to an attestation. The forge_contract_core
  family `failureforge_handoff_attestation_payload` carries it as
  `hardening_report_hash` (RFC-FFQ-01).
