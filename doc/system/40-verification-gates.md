# 40 Verification Gates

The local proof gate is `bash scripts/ci_gate.sh`.

It writes evidence under `reports/failureforge-verification/latest/` and runs:

- dependency import check
- `python3 -m pytest`
- sandbox demo run
- receipt schema/hash verification
- deterministic replay
- no-canonical-mutation verification
- target adapter schema and preflight tests
- external target-source adapter requirement tests
- adapter required-command and forbidden-source-path tests
- adapter-aware external-source replay tests
- replay command context tests for adapter-backed receipts
- canonical source fingerprint tests
- fail-closed canonical mutation tests
- CLI canonical mutation exit tests
- CLI replay canonical mutation exit tests
- replay canonical mutation guard tests
- replay mismatch artifact status tests
- CLI replay receipt validation tests
- verify-receipts malformed JSON tests
- CLI adapter load validation tests
- documentation assembly

Supporting commands:

- `bash scripts/verify_receipts.sh`
- `bash scripts/replay_failure.sh sandbox/receipts/<receipt>.json`
- `bash scripts/verify_no_canonical_mutation.sh`
- `bash doc/system/BUILD.sh`

## Which CI runs for which change

A change to documentation runs the Documentation CI and no code CI.
A change to any other file runs the code CI.
A change to both runs both.
No workflow runs on a schedule.

The code workflow `.github/workflows/ci.yml` (job `scripts/ci_gate.sh`) uses a workflow-level `paths` filter on `push` and on `pull_request`:

```yaml
paths:
  - '**'
  - '!docs/**'
  - '!doc/**'
  - '!**/*.md'
  - 'README.md'
  - 'doc/system/00-purpose.md'
  - 'sandbox-targets/**'
```

The last matching pattern wins, so the re-includes come last.
A change to `.github/workflows/**` is code, so it runs the code CI.

The re-includes are documentation that code reads:

- `README.md`: `tests/test_slice_10_governance_reconciliation.py` reads it.
- `doc/system/00-purpose.md`: the same test reads it and checks the role statements.
- `sandbox-targets/**`: this is the canonical demo target. The sandbox runner hashes every file in it, including its `README.md`. The no-canonical-mutation gate compares that hash.

`scripts/ci_gate.sh` also runs `doc/system/BUILD.sh`.
The Documentation CI runs the same build on every documentation change, and the gate still runs it on every code change.
If a test or script starts to read another documentation path, add that path as a re-include.

The Documentation CI is `.github/workflows/documentation.yml`.
It runs on a change under `docs/`, under `doc/`, to any `*.md` file, or to its own workflow file.
It runs `bash doc/system/BUILD.sh` and then `git diff --exit-code -- doc`.
`doc/FFGSYSTEM.md` is not committed, so the diff step finds nothing by design.
The build validates the parts. It does not compare against a committed reference (see KI-FFG-20260930-001).

This repository has no secret scan workflow.
If a secret scan is added, it must run on every change and must not use a path filter.

Warning: do not add a required status check on a path-filtered workflow.
The check stays pending forever when the filter skips the workflow, and the merge stays blocked.
