# Local Ollama validation ? 2026-10-31

Actual inference through http://127.0.0.1:11434/api/chat; no scripted provider was substituted. The ticket remains an authored educational fixture.

Ollama version: 0.31.1. Sequential attempts, temperature 0, eight-step budget, 90-second cooperative run budget, 30-second per-call timeout. Same final prompt, fixture, verifier and host settings for all six final trials. Model loading/cache state was not standardized; timing is descriptive only.

## Model identities

- `llama3.2:3b`: `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
- `mistral:7b`: `6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf`

## Final observed trials

| Model | Trial | Accepted | Steps | Seconds | Stop |
| --- | --- | --- | --- | --- | --- |
| llama3.2:3b | 1 | True | 4 | 2.088 | accepted |
| llama3.2:3b | 2 | True | 4 | 1.630 | accepted |
| llama3.2:3b | 3 | True | 4 | 1.530 | accepted |
| mistral:7b | 1 | False | 8 | 3.588 | step_budget |
| mistral:7b | 2 | False | 8 | 3.913 | step_budget |
| mistral:7b | 3 | False | 8 | 3.962 | step_budget |

Llama read the actual module, selected an exact replacement, passed five verifier checks and requested finish. It skipped the prompt-requested pre-edit test; that step is guidance, not a host-enforced condition. Final-source verification is enforced. Mistral repeatedly read the same module; no edit or test occurred. The step budget stopped it without accepting a patch.

## Development attempts retained

- `live-initial-llama` and `live-initial-mistral`: original generated union schema caused HTTP 400. A bounded diagnostic request exposed the server error: failed to initialize samplers / failed to parse grammar. Initial adapter only retained the HTTP status; the new adapter preserves server error bodies.
- `live-schemafix-llama`: after adopting a simple object generation schema, Llama proposed replacement text absent from the source; exact-match validation stopped it.
- `live-schemafix-mistral`: eight repeated reads, then step-budget stop.
- `live-workflow-llama`: after clarifying the read/edit/test/finish workflow, accepted in four actions.
- `live-workflow-mistral`: still eight reads, then stop.

These tuning attempts are separate from the final six trials. Prompt development used the same ticket, so final results are development-set observations, not independent held-out evaluation. No attempt was deleted or counted as a success because of its final message.

## Code changes verified

- Simple provider object schema, strict host action union unchanged.
- Live mode defaults to llama3.2:3b; --model and HARNESS_MODEL overrides.
- HTTP errors retain bounded response bodies; incomplete responses fail closed.
- model-exchanges.json preserves request context, actual provider response and timing/token fields.
- Explicit UTF-8 file reads for generated source on Windows.
- scripts/run_local_trials.py records installed model digests and Ollama version, creates fresh runs and retains outcomes.

## Verification

- 16 pytest tests passed, including generation-schema transport, incomplete-response rejection and strict host rejection of extra action fields.
- `ollama-final-baseline` and `ollama-final-candidate`: all seven scripted contract outcomes matched; baseline gate passed.
- `live-action-replay`: actual Llama action sequence reexecuted tools and checks in a fresh workspace and was accepted.
- Existing model-independent tests remain necessary: six inference attempts cannot exercise all host failure paths.

Execution still uses the local user?s OS permissions, not a hostile-code sandbox. The task-specific test result is evidence for this benign repair, not a security proof.
