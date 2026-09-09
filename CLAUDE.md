# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FailureForge is a sandbox-only failure-harvesting subsystem and read-only governance evidence bridge for Forge. It runs multi-agent lanes (chaos, mutation, reproduction, classification, edge-case) against copied target workspaces, produces immutable, schema-validated receipts and hardening reports, and bridges read-only evidence into governance (ERA/AAR) without ever claiming fixes or bypassing operator review. Implementation-complete planning artifacts for its 24 shipped slices are archived under `Drive/Forge/Plans/Implemented/failureforge` (see `docs/plans/IMPLEMENTED_PLAN_ARCHIVES.md`).

## Common Commands

- Install (editable, with dev deps): `pip install -e ".[dev]"`
- Run tests: `pytest` (testpaths = `tests`)
- Lint/format: `ruff check .`, `ruff format .`
- Demo run:
  ```bash
  bash scripts/run_sandbox_once.sh
  bash scripts/verify_receipts.sh
  bash scripts/replay_failure.sh sandbox/receipts/<receipt-id>.json
  ```
- CLI (`src/failureforge/cli.py`): `run-sandbox`, `replay`, `verify-receipts`, `morning-report`

## Architecture

```
failureforge/
  schemas/                  # receipt, report, promotion, approval, cluster, adjudication contracts
  fixtures/{valid,invalid}/ # contract fixtures
  src/failureforge/
    agents/                 # edge_case, chaos, mutation, reproduction, classification
    adjudication/           # NeuroForge provider comparison (Slice 09)
    clustering/centipede.py # root-cause clustering (Slice 08)
    integrations/           # ERA export + AAR seed builders (Slice 10)
    runtime/target_adapter.py # target adapter guard (Slice 11)
    runtime/sandbox.py      # SandboxRunner: copies workspace, runs lanes, writes receipts
    runtime/replay.py       # replay helper used by replay_failure.sh
    reporting/scorer.py     # ranking + HardeningReport generator (Slice 03)
    validation/             # JSON Schema + receipt-hash validators
    cli.py                  # run-sandbox, replay, verify-receipts, morning-report
  tests/                    # pytest suite for Slices 01-24
  sandbox/{workspaces,runs,receipts,reports}/
  sandbox-targets/example-repo/  # tiny target used by the demo run
  scripts/                  # run_sandbox_once.sh, replay_failure.sh, verify_receipts.sh
```

Cross-repo: Slices 04-06 and the governance-reconciliation half of Slice 10 exercise the FailureForge -> DataForge Local handshake, whose service/router code lives in the sibling `dataforge-Local` repo (requires FastAPI). Those tests skip cleanly when this repo is checked out standalone; they run when `dataforge-Local` is present alongside this repo. DataForge Local owns the operator API and persistence-facing integration under `dataforge-Local/app/failureforge/`.

## Notes

**Read this before pointing FailureForge at any untrusted target.** The "sandbox" is a **filesystem copy, not an OS isolation boundary**. The runner copies the target into `sandbox/workspaces/` and then imports and executes the target's `registry.py` **in-process**, with the full privileges of the runner — nothing constrains sockets, filesystem writes outside the workspace, or spawned processes. The `canonical_source_hash_before`/`_after` guard is detective, not preventive, and is scoped only to the canonical source tree (it fails the run with exit code `5` if that directory changed, but does not stop other side effects). The demo target ships intentionally safe code; before running a non-demo or untrusted target, wrap the run in real OS isolation (container, seccomp, read-only root FS, no network).

Core doctrine:
- All destructive testing happens against **copied workspaces**, never canonical repos.
- Receipts are immutable after write; modifying one invalidates its hash and fails verification.
- No direct patch promotion — operator approval and SMITH handoff are mediated by explicit promotion/approval receipts and FSM checks.
- Every reproducible failure has a replay command; non-reproducible failures are explicitly marked.
- ERA exports and AAR seeds are read-only bridge artifacts — they cannot claim fixes, bypass operator review, or mark evidence safe to autofix.
- Non-demo targets require a target adapter (declared attack families + canonical mutation guards) and pass adapter preflight before any workspace copy.
