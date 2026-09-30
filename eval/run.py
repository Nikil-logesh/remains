"""Offline corpus runner: python -m eval.run --corpus ... --challenger ..."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .promotion import promotion_gate
from .scoring import score_attempts


def _read(path: str) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8-sig")
    if Path(path).suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    value = json.loads(text)
    return value if isinstance(value, list) else value.get("items", value.get("attempts", []))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--challenger", required=True)
    parser.add_argument("--incumbent")
    args = parser.parse_args(argv)
    challenger = score_attempts(_read(args.challenger), _read(args.corpus))
    report = {"challenger": challenger}
    if args.incumbent:
        incumbent = score_attempts(_read(args.incumbent), _read(args.corpus))
        report["incumbent"] = incumbent
        report["promotion"] = promotion_gate(challenger, incumbent)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
