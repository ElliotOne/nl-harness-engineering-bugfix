# nl-harness-engineering-bugfix

A Python companion for issue #52: a bounded coding-agent harness repairs a real, runnable shipping-price bug and checks the resulting file. The ticket and replay actions are authored educational fixtures, not a customer incident. Actual local-model attempts are retained separately from authored regression actions.

## Overview

At exactly 5000 pence, the supplied function charges 499 pence when it should charge zero. The harness supplies context, accepts one typed JSON action per turn, applies permitted edits in a fresh temporary directory, runs five harness-owned acceptance checks, and writes evidence before returning a decision.

## What This Project Demonstrates

- Four typed actions: read, exact replacement, test, finish.
- Exact path allowlists; tests and instructions cannot be changed through tools.
- File-hash-bound test evidence: any subsequent edit invalidates completion.
- Step, wall-clock, model-call and test budgets with fail-closed outcomes.
- Seven scripted regression cases, baseline comparison, and tested local-model execution.
- JSONL observations, raw rejected actions, input hashes, candidate files and unified diffs.

## Prerequisites

Python 3.13+, pip; Ollama running on localhost with a downloaded chat model that supports JSON-schema output. Use an isolated disposable machine/container for untrusted generated Python. Dependencies: Pydantic 2; pytest for development.

## Quick Start

Run from this companion directory. Use a unique output directory for every run.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[test]"
.venv/Scripts/python -m pytest -q
.venv/Scripts/bugfix-harness suite --out runs/baseline
.venv/Scripts/bugfix-harness suite --out runs/candidate --baseline runs/baseline/suite.json
.venv/Scripts/bugfix-harness replay --actions runs/baseline/boundary-fix/actions.json --out runs/replayed
```

On POSIX use `.venv/bin/python` and `.venv/bin/bugfix-harness`.

Live run (the CLI defaults to live mode):

```powershell
.venv/Scripts/bugfix-harness live --model llama3.2:3b --out runs/live-001
.venv/Scripts/bugfix-harness live --model mistral:7b --out runs/live-002
.venv/Scripts/python scripts/run_local_trials.py --out runs/local-trials
```

The loopback adapter calls `/api/chat` with a simple object generation schema, then strictly validates the returned action with the Pydantic discriminated union. The installed server rejected the original union grammar; generation constraints do not replace host validation. Live runs save request/response exchanges and reject incomplete generation. No model is downloaded. Temperature zero does not guarantee identical decisions.

Final local trials on Ollama 0.31.1: llama3.2:3b completed 3/3 attempts in four actions (1.530?2.088 seconds); mistral:7b completed 0/3, repeating read until the eight-step budget. These are sequential development-ticket observations, not held-out model-quality estimates. Earlier failed integration and prompt-development attempts are preserved. See `docs/live-validation.md`.

## Configuration

`harness.toml` sets max_steps=8, max_seconds=90, test_timeout=5, model_timeout=30, max_response_bytes=32768. Each key has an integer `HARNESS_` environment override, e.g. `HARNESS_MAX_STEPS`. `--model` selects the live model, then `HARNESS_MODEL`, then `llama3.2:3b`. Omitting the mode selects live execution. The endpoint is fixed to 127.0.0.1:11434. Response-size bounds apply to both the HTTP envelope and action. No token-cost meter is implemented.

## How It Works

A fresh copy of `fixture/shipping.py` is the only editable file. `fixture/AGENTS.md` is provided as initial context and is also readable. The host parses actions through a discriminated Pydantic union with forbidden extra fields. Replace requires one exact match. Test invokes an absolute harness-owned verifier with `python -I`, a fixed argument list, and a timeout. Five checks cover zero, below, at, above, and negative subtotals. A successful test binds to the current source hash; finish succeeds only for that same hash. Errors terminate the run rather than triggering unbounded repair retries.

The suite compares expected pass/fail AND stop reason, requires all contract cases to pass, rejects a changed case-file hash or case-ID set against a baseline, and exits 1 on gate failure. It is deliberately a strict gate, not a statistical model-quality comparison. Baselines must be reviewed and kept in a separate CI artifact; updating expectations automatically defeats the gate.

## Project Structure

- `src/bugfix_harness/core.py`: contracts, provider adapters, execution and evidence.
- `src/bugfix_harness/cli.py`: suite, replay and live entry points.
- `fixture/`: intentionally buggy input and repository rules.
- `verifier.py`: five protected acceptance checks.
- `cases.json`: seven authored action sequences with expected outcomes.
- `tests/`: control and failure-path tests.
- `evidence/`: actual offline runs; absolute temporary paths in logs are machine-specific.
- `docs/research.md`: eleven primary sources and implementation decisions.

## Control Guarantees

Tool-mediated edits are limited to shipping.py. Completion requires current-source test success. Invalid actions, provider failure, test timeout, exhausted steps and deadlines fail closed. Output directories cannot be reused. Manifests identify fixture, instructions, prompt, verifier, harness implementation, settings, Python and OS; suite summaries identify the case dataset. These are unsigned local records, not a tamper-proof audit trail.

**Execution boundary:** a temporary directory and `-I` do not isolate Python from the host. Candidate code runs with the current user's OS permissions, can inspect files/network, modify the verifier outside the tool path, forge test exit status, or spawn processes. Do not use this runner to grade hostile code. For production, run the candidate and tests in a disposable resource-limited container/VM, without host secrets, with read-only verifier mounts, restricted egress, process-tree cleanup, output quotas and independently collected results. The acceptance tests establish bounded behavior for this benign fixture, not a security proof. Test logs are not disk-quota bounded. urllib timeouts bound socket operations; the wall clock is checked between operations and is not a hard process supervisor.

## Tests

`python -m pytest -q`: 16 tests, including seven fixture cases, exact action replay, strict schema rejection, timeout and provider failure. Scripted evidence matches seven expected outcomes, comprising one accepted fix and six expected stops. Separate live evidence records three attempts for each model, actual tool observations, test logs and patches. Replay reruns tools and acceptance checks; it does not return cached observations. The reported completion counts describe only these six local attempts; no general benchmark result is claimed.

## License

No standalone license is granted by this sample. Confirm licensing before external redistribution.

## Contributing

Add reproducible tickets with reference behavior, protected checks and failure cases. Keep a held-out task set for model-quality evaluation. Review baseline changes independently of harness changes.
