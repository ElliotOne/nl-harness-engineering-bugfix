# Validation ? 2026-10-31

- Python 3.13.2; 13 tests passed. Final invocation used a workspace-local pytest basetemp because the shared OS pytest temporary root became inaccessible.
- `evidence/verified-baseline/suite.json`: 7/7 contract outcomes matched.
- `evidence/verified-candidate/suite.json`: baseline comparison passed.
- `evidence/verified-replay/report.json`: replay reexecuted tests and accepted the patch.
- `evidence/rejected-comparison/suite.json`: changed baseline case hash caused exit 1.
- All referenced SVGs parse as XML. Browser-rendered desktop, mobile and icon contact sheet visually inspected; no clipping or text collisions found.
- Two dark explanatory figures, each with a dedicated mobile variant; Mermaid architecture source remains in the issue. Cover SVG plus PNG; black 1.3-unit stroke clamp icon with one solid component.
- Revised issue is approximately 2,150 prose words, plus eight compact code/configuration/Mermaid snippets: estimated 10?12 minute technical read.
- Eleven primary-source resources were read before drafting. Follow-up verification re-read core accounts and added four primary resources; the fifteen-resource ledger records claim checks, decisions and limits.
- No live model was called. No general model performance, production incident, or security-isolation claim is made.


## Superseding live verification

The earlier offline-only qualification describes the initial draft. Actual Ollama inference is now tested: see [live-validation.md](live-validation.md) for six final trials, preserved development failures, exact model identities, 16 passing tests, and a replay of model-generated actions. The revised issue is approximately 2,290 prose words plus compact snippets, targeting a 10?12 minute technical read. Graphics continue to describe the same execution and verification boundaries.
