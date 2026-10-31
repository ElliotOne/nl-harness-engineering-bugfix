import json
from pathlib import Path
import pytest
from bugfix_harness.core import ACTION, Replay, Settings, run
ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "cases.json").read_text())
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_contract_cases(tmp_path, case):
    report = run(ROOT, tmp_path / "run", Replay(case["actions"]), "test")
    assert (report["passed"], report["reason"]) == (case["expected_pass"], case["expected_reason"])
    assert (ROOT / "fixture/shipping.py").read_text().count("> 5000") == 1
    assert (tmp_path / "run/manifest.json").exists()

def test_exact_replay_reexecutes_checks(tmp_path):
    first = tmp_path / "first"
    run(ROOT, first, Replay(CASES[0]["actions"]), "test")
    actions = json.loads((first / "actions.json").read_text())
    second = tmp_path / "second"
    assert run(ROOT, second, Replay(actions), "replay")["passed"]
    assert (second / "test-4.log").exists()

@pytest.mark.parametrize("value", [
    '{"op":"test","command":"echo ok"}', '{"op":"shell"}',
    '{"op":"replace","path":"shipping.py","old":"","new":"x"}'
])
def test_schema_rejects_extra_authority(value):
    with pytest.raises(ValueError): ACTION.validate_json(value)

def test_timeout_is_failure(tmp_path):
    actions = [{"op":"replace", "path":"shipping.py", "old":"def shipping_pence",
                "new":"import time; time.sleep(3)\ndef shipping_pence"}, {"op":"test"}]
    report = run(ROOT, tmp_path / "run", Replay(actions), "test", Settings(test_timeout=1))
    assert report["reason"] == "execution_error"
    assert not report["passed"]

def test_failed_model_call_writes_report(tmp_path):
    class Broken:
        def next(self, messages, timeout): raise TimeoutError("provider unavailable")
    assert run(ROOT, tmp_path / "run", Broken(), "broken")["reason"] == "execution_error"


@pytest.mark.parametrize("envelope,accepted", [
    ({"done": True, "done_reason": "stop", "message": {"content": '{"op":"test"}'}}, True),
    ({"done": True, "done_reason": "length", "message": {"content": '{"op":"test"}'}}, False),
])
def test_ollama_transport_schema_and_completion(monkeypatch, envelope, accepted):
    import io
    import bugfix_harness.core as core
    def fake_urlopen(request, timeout):
        payload = json.loads(request.data)
        assert payload["format"]["type"] == "object"
        assert payload["stream"] is False
        assert payload["options"]["temperature"] == 0
        return io.BytesIO(json.dumps(envelope).encode())
    monkeypatch.setattr(core, "urlopen", fake_urlopen)
    provider = core.Ollama("local-model", 32768)
    if accepted:
        assert core.ACTION.validate_json(provider.next([], 5)).op == "test"
        assert provider.exchanges[0]["response"] == envelope
    else:
        with pytest.raises(ValueError, match="incomplete"): provider.next([], 5)


def test_generation_schema_does_not_replace_host_validation(monkeypatch):
    import io
    import bugfix_harness.core as core
    envelope = {"done": True, "message": {"content": '{"op":"test","path":"shipping.py"}'}}
    monkeypatch.setattr(core, "urlopen", lambda *a, **kw: io.BytesIO(json.dumps(envelope).encode()))
    with pytest.raises(ValueError):
        core.ACTION.validate_json(core.Ollama("local-model", 32768).next([], 5))
