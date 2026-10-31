"""Sequential local-model trials; preserves every run, including failures."""
import argparse
import json
from pathlib import Path
from urllib.request import urlopen
from bugfix_harness.core import Ollama, run, settings

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--models", nargs="+", default=["llama3.2:3b", "mistral:7b"])
    args = parser.parse_args()
    if not 1 <= args.trials <= 10: parser.error("trials must be between 1 and 10")
    root = Path.cwd()
    args.out.mkdir(parents=True, exist_ok=False)
    inventory = {}
    for name in ["version", "tags"]:
        with urlopen("http://127.0.0.1:11434/api/" + name, timeout=5) as response:
            inventory[name] = json.load(response)
    (args.out / "environment.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    installed = {m["name"] for m in inventory["tags"]["models"]}
    if not set(args.models) <= installed: raise ValueError("requested model not installed")
    cfg = settings(root)
    rows = []
    for index, model in enumerate(args.models):
        for trial in range(1, args.trials + 1):
            out = args.out / f"model-{index + 1}-trial-{trial}"
            report = run(root, out, Ollama(model, cfg.max_response_bytes), "ollama:" + model, cfg)
            row = {"model": model, "trial": trial, "directory": out.name, **report}
            rows.append(row)
            (args.out / "summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
            print(json.dumps(row), flush=True)

if __name__ == "__main__": main()
