# Research ledger

Read on 2026-10-31 before implementation and drafting. Eleven distinct primary resources; short paraphrases record what was used and its limits. These are design inputs, not evidence of a live model run.

## 1. [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/)

Repository legibility, feedback loops and mechanical constraints are engineering responsibilities. Applied here as a small context pack, an explicit tool boundary and executable acceptance checks. This example is independently built; no OpenAI productivity numbers are adopted.

## 2. [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

Documents premature completion and loss of continuity across sessions. Applied as checked completion and external run artifacts. This implementation does not implement multi-session resumption or the initializer/coding-agent architecture.

## 3. [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

Separates tasks, trials, graders, transcripts and outcomes. Applied as action traces plus tests of the actual candidate file. Scripted trials validate harness behavior; they do not establish model task success.

## 4. [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

Distinguishes predefined workflows from model-directed tool use and recommends simple composable designs. Applied as one bounded tool loop with separate deterministic verification; no multi-agent orchestration.

## 5. [Promptfoo introduction](https://www.promptfoo.dev/docs/intro/)

Describes declarative evaluations, assertions, provider integrations and CI usage. Applied as explicit case expectations and a nonzero failing gate. Promptfoo is a possible replacement for evaluation plumbing, not a dependency of this project.

## 6. [LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types)

Distinguishes offline curated-data evaluation from online monitoring and describes code-based and model-based grading. Applied as offline regression cases with deterministic grading. No online monitoring is implemented.

## 7. [MLflow GenAI evaluation](https://mlflow.org/docs/latest/genai/eval-monitor/)

Connects datasets, traces, feedback and scorers. Applied as file-backed evidence tied to case IDs; MLflow would help when shared trace search and dataset management become necessary. No MLflow server is required.

## 8. [OpenAI Evals repository](https://github.com/openai/evals)

Provides a framework and registry for evaluating models and LLM systems, including custom private evals. Applied as task-specific cases rather than a generic benchmark score. The project is not an integration with OpenAI Evals.

## 9. [SWE-bench evaluation guide](https://www.swebench.com/SWE-bench/guides/evaluation/)

Evaluates generated patches by running repository tests in containers. Distinguishes unresolved tasks from infrastructure errors and warns about result caching by run ID. Applied as fresh workspaces, distinct stop reasons and unique output directories. This tiny authored fixture is not SWE-bench and has no benchmark claim.

## 10. [Python 3.13 subprocess](https://docs.python.org/3.13/library/subprocess.html)

Documents argument-vector execution, explicit cwd, process exit status and timeouts. Applied as a fixed interpreter/verifier command with shell=False. A subprocess timeout is not a security sandbox or a guarantee that all descendant processes are stopped.

## 11. [pytest invocation guide](https://docs.pytest.org/en/stable/how-to/usage.html)

Documents python -m pytest, test selection and configuration. Applied as repository-scoped tests; acceptance checks use standard-library unittest in a separate interpreter to avoid an extra runtime dependency in the candidate workspace.

## Synthesis

The implementation combines a coding-agent execution harness with a regression harness. Frozen actions test host behavior. Fresh model trials test the combined system. Tests own observable acceptance; a model owns proposed edits. Hashes identify inputs but do not create tamper-proof evidence. The example is intentionally one locally authored shipping ticket so every claimed result can be reproduced without a vendor account.


## Follow-up content verification ? 2026-10-31

Re-read the OpenAI harness engineering account, both Anthropic long-running harness accounts, and the Anthropic evaluation guide against the issue and Python implementation. Added four distinct primary resources below, bringing the ledger to fifteen. The original eleven-resource research preceded drafting; these four were read during revision.

### 12. [LangChain: The Anatomy of an Agent Harness](https://www.langchain.com/blog/the-anatomy-of-an-agent-harness)

Broadens the definition to runtime context, tools, state, infrastructure and control. Revision explicitly separates the execution harness from the regression suite and identifies omitted context-management features. The small tool set remains a task-specific design choice.

### 13. [Birgitta B?ckeler: Harness engineering for coding agent users](https://martinfowler.com/articles/harness-engineering.html)

Distinguishes product-provided execution machinery from repository-specific guidance and feedback. Revision explains that teams can configure an existing coding agent rather than implement a replacement. The five implementation steps are labelled the author's synthesis.

### 14. [Anthropic: Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)

Describes testing simplifications as models and task requirements change. Revision recommends measuring component changes individually. Its multi-agent design and results are not attributed to this companion.

### 15. [Ollama: Structured outputs](https://docs.ollama.com/capabilities/structured-outputs)

Documents JSON Schema in the chat request's format field and validation of the returned content. Matches the adapter's intended request pattern; no live inference compatibility or performance claim was added.

### Claim checks and resulting edits

| Claim or ambiguity | Verification | Resolution |
| --- | --- | --- |
| Harness engineering could read as only testing or restrictions | LangChain anatomy; OpenAI engineering account; B?ckeler's guide | Added definition covering context, workspace, tools, state, execution and feedback; five practical steps. |
| Runtime harness and evaluation harness were easy to conflate | Anthropic eval guide; core.py and cli.py | Named the execution loop and scripted regression suite separately. |
| Durable run files might imply resumable sessions | Anthropic long-running harness account; in-memory messages in core.py | Explicitly states that session resumption and compaction are not implemented. |
| Protected tests might imply hostile-code isolation | subprocess invocation and verifier loading candidate Python | Calls them harness-owned and scopes allowlists to tool-mediated access; retains the explicit OS-permission limitation. |
| Accepted might imply merge-ready | Finish branch, verifier and report | Scoped acceptance to this fixture; normal review and CI remain necessary. |
| Replay might imply adaptive or fully equivalent reruns | Replay.next ignores messages; manifests written but not checked | Explains non-adaptive replay and manual manifest comparison. |
| Reproduction claims | Existing verified evidence | 7 contract cases matched; valid candidate gate passed; incompatible dataset blocked; replay accepted. No new model measurements. |
| Read length | MDX prose extracted excluding snippets and tags | About 2,150 prose words plus eight compact snippets, including Mermaid; estimated 10?12 minutes with code and figure inspection. |

No runtime or graphics changes were required by this editorial review. Existing offline results are retained; no live model was called.


## Local-inference implementation follow-up

The earlier statement that no live model was called applies to the editorial verification at that time and is superseded by docs/live-validation.md. The fifteen-source ledger is extended below.

### 16. [Ollama: Generate a chat message](https://docs.ollama.com/api/chat)

Checked the chat request format, non-streaming response, completion reason, timing fields and token counts. Actual local tests exposed a grammar rejection for the generated union schema. The adapter now uses a simpler generation schema and retains strict Python validation, provider responses and bounded HTTP diagnostics. Three final trials per installed model are recorded without claiming held-out performance.
