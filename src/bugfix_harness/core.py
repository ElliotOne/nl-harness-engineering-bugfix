from __future__ import annotations
import difflib
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from typing import Annotated, Literal, Protocol
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
class Read(Strict):
    op: Literal["read"]
    path: str
class Replace(Strict):
    op: Literal["replace"]
    path: str
    old: str = Field(min_length=1, max_length=16000)
    new: str = Field(max_length=16000)
class Test(Strict):
    op: Literal["test"]
class Finish(Strict):
    op: Literal["finish"]
Action = Annotated[Read | Replace | Test | Finish, Field(discriminator="op")]
ACTION = TypeAdapter(Action)
class Settings(Strict):
    max_steps: int = Field(default=8, ge=1, le=100)
    max_seconds: int = Field(default=90, ge=1, le=600)
    test_timeout: int = Field(default=5, ge=1, le=60)
    model_timeout: int = Field(default=30, ge=1, le=120)
    max_response_bytes: int = Field(default=32768, ge=128, le=1000000)

def settings(root: Path) -> Settings:
    values = tomllib.loads((root / "harness.toml").read_text(encoding="utf-8"))
    for key in Settings.model_fields:
        if (value := os.getenv("HARNESS_" + key.upper())) is not None:
            values[key] = int(value)
    return Settings(**values)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

class Provider(Protocol):
    def next(self, messages: list[dict[str, str]], timeout: float) -> str: ...

class Replay:
    def __init__(self, actions: list[dict]): self.actions = iter(actions)
    def next(self, messages: list[dict[str, str]], timeout: float) -> str:
        return json.dumps(next(self.actions))

# Deliberately simple generation grammar for local Ollama compatibility.
# Conditional fields remain strictly validated by ACTION, not trusted to the model.
OLLAMA_SCHEMA = {
    "type": "object", "properties": {
        "op": {"type": "string", "enum": ["read", "replace", "test", "finish"]},
        "path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}},
    "required": ["op"], "additionalProperties": False,
}

class Ollama:
    def __init__(self, model: str, limit: int):
        self.model, self.limit = model, limit
        self.exchanges: list[dict] = []
    def next(self, messages: list[dict[str, str]], timeout: float) -> str:
        # Fixed loopback endpoint: credentials and arbitrary remote URLs are unnecessary.
        body = json.dumps({"model": self.model, "messages": messages,
                           "stream": False, "format": OLLAMA_SCHEMA,
                           "options": {"temperature": 0}}).encode()
        req = Request("http://127.0.0.1:11434/api/chat", body,
                      {"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=timeout) as response:
                raw = response.read(self.limit + 1)
        except HTTPError as error:
            detail = error.read(self.limit).decode(errors="replace")
            self.exchanges.append({"request": json.loads(body), "http_error": detail})
            raise RuntimeError(f"Ollama HTTP {error.code}: {detail}") from error
        if len(raw) > self.limit: raise ValueError("model response too large")
        envelope = json.loads(raw)
        self.exchanges.append({"request": json.loads(body), "response": envelope})
        if not envelope.get("done") or envelope.get("done_reason") == "length":
            raise ValueError("incomplete model generation")
        return envelope["message"]["content"]

def run(root: Path, out: Path, provider: Provider, label: str,
        config: Settings | None = None) -> dict:
    cfg = config or settings(root)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started + cfg.max_seconds
    prompt = (root / "prompt.txt").read_text(encoding="utf-8")
    tracked = ["fixture/shipping.py", "fixture/AGENTS.md", "verifier.py", "prompt.txt"]
    manifest = {p: digest((root / p).read_bytes()) for p in tracked}
    manifest.update({"config": cfg.model_dump(), "python": sys.version,
                     "platform": platform.platform(), "provider": label,
                     "core": digest(Path(__file__).read_bytes())})
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    messages = [{"role": "system", "content": prompt},
                {"role": "user", "content": (root / "fixture/AGENTS.md").read_text(encoding="utf-8")}]
    tested_hash = None
    reason, passed = "step_budget", False
    actions = []
    with tempfile.TemporaryDirectory(prefix="bugfix-") as folder:
        work = Path(folder)
        shutil.copyfile(root / "fixture/shipping.py", work / "shipping.py")
        original = (work / "shipping.py").read_text(encoding="utf-8")
        with (out / "trace.jsonl").open("w", encoding="utf-8") as trace:
            for step in range(1, cfg.max_steps + 1):
                raw = None
                try:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0: reason = "deadline"; break
                    raw = provider.next(messages, min(remaining, cfg.model_timeout))
                    if time.monotonic() >= deadline: reason = "deadline"; break
                    if len(raw.encode()) > cfg.max_response_bytes:
                        raise ValueError("action too large")
                    action = ACTION.validate_json(raw)
                    actions.append(action.model_dump())
                    if isinstance(action, (Read, Replace)):
                        allowed = {"shipping.py"} if isinstance(action, Replace) else {"shipping.py", "AGENTS.md"}
                        if action.path not in allowed: raise PermissionError("path not allowed")
                    if isinstance(action, Read):
                        source = work / action.path if action.path == "shipping.py" else root / "fixture/AGENTS.md"
                        observation = {"text": source.read_text(encoding="utf-8")}
                    elif isinstance(action, Replace):
                        source = work / "shipping.py"
                        text = source.read_text(encoding="utf-8")
                        if text.count(action.old) != 1: raise ValueError("old text must match once")
                        source.write_text(text.replace(action.old, action.new), encoding="utf-8")
                        tested_hash = None
                        observation = {"edited": True}
                    elif isinstance(action, Test):
                        remaining = deadline - time.monotonic()
                        if remaining <= 0: reason = "deadline"; break
                        # Output goes to disk: truncate only the observation, not evidence.
                        log = out / f"test-{step}.log"
                        with log.open("wb") as stream:
                            result = subprocess.run(
                                [sys.executable, "-I", str((root / "verifier.py").resolve()),
                                 str(work / "shipping.py")], cwd=work,
                                stdout=stream, stderr=subprocess.STDOUT,
                                timeout=min(remaining, cfg.test_timeout), check=False)
                        ok = result.returncode == 0
                        tested_hash = digest((work / "shipping.py").read_bytes()) if ok else None
                        observation = {"tests_passed": ok, "returncode": result.returncode,
                                       "output": log.read_bytes()[-4000:].decode(errors="replace")}
                    else:
                        passed = tested_hash == digest((work / "shipping.py").read_bytes())
                        reason = "accepted" if passed else "unverified_finish"
                        observation = {"accepted": passed, "reason": reason}
                    messages.extend([{"role": "assistant", "content": raw},
                                     {"role": "user", "content": json.dumps(observation)}])
                    event = {"step": step, "action": action.model_dump(), "observation": observation}
                    trace.write(json.dumps(event) + "\n"); trace.flush()
                    if isinstance(action, Finish): break
                except Exception as error:
                    reason = "policy_denied" if isinstance(error, PermissionError) else "execution_error"
                    trace.write(json.dumps({"step": step, "raw": raw, "error": type(error).__name__,
                                            "detail": str(error), "reason": reason}) + "\n")
                    break
        final = (work / "shipping.py").read_text(encoding="utf-8")
        (out / "candidate.py").write_bytes(final.encode("utf-8"))
        (out / "patch.diff").write_text("".join(difflib.unified_diff(
            original.splitlines(True), final.splitlines(True), "a/shipping.py", "b/shipping.py")), encoding="utf-8")
    if time.monotonic() > deadline:
        passed, reason = False, "deadline"
    report = {"passed": passed, "reason": reason, "steps": len(actions),
              "elapsed_seconds": round(time.monotonic() - started, 3),
              "candidate_sha256": digest(final.encode())}
    if isinstance(provider, Ollama):
        (out / "model-exchanges.json").write_text(
            json.dumps(provider.exchanges, indent=2), encoding="utf-8")
    for name, value in [("report.json", report), ("actions.json", actions)]:
        (out / name).write_text(json.dumps(value, indent=2), encoding="utf-8")
    return report
