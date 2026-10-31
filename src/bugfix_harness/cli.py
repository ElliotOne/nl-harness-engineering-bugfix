import argparse
import json
import os
from pathlib import Path
from .core import Ollama, Replay, digest, run, settings

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", default="live", choices=["suite", "replay", "live"])
    parser.add_argument("--model", default=os.getenv("HARNESS_MODEL", "llama3.2:3b"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--actions", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    if args.mode == "suite":
        cases = json.loads((root / "cases.json").read_text())
        rows = {}
        for case in cases:
            report = run(root, args.out / case["id"], Replay(case["actions"]), "scripted-fixture")
            rows[case["id"]] = {"contract_pass": report["passed"] == case["expected_pass"]
                                and report["reason"] == case["expected_reason"], **report}
        gate = all(row["contract_pass"] for row in rows.values())
        if args.baseline:
            baseline = json.loads(args.baseline.read_text())
            gate = gate and digest((root / "cases.json").read_bytes()) == baseline["cases_sha256"] and rows.keys() == baseline["cases"].keys() and all(
                not old["contract_pass"] or rows[key]["contract_pass"]
                for key, old in baseline["cases"].items())
        summary = {"gate_pass": gate, "cases_sha256": digest((root / "cases.json").read_bytes()), "cases": rows}
        (args.out / "suite.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
        raise SystemExit(0 if gate else 1)
    cfg = settings(root)
    if args.mode == "live":
        model = args.model
        provider, label = Ollama(model, cfg.max_response_bytes), "ollama:" + model
    else:
        if not args.actions: parser.error("replay requires --actions")
        provider, label = Replay(json.loads(args.actions.read_text())), "recorded-actions"
    report = run(root, args.out, provider, label, cfg)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)

if __name__ == "__main__": main()
