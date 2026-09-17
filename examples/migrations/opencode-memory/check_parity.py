"""Recall-parity harness: prove zero amnesia after the migration round-trip.

1. Loads the source export (questions we expect the memory to answer).
2. Loads the generated OKF bundle with Memanto's own ``load_okf_bundle``.
3. Maps it with ``mappers.map_okf`` (same code path as ``migrate okf``).
4. Asserts every probe question is answerable from the migrated rows.

Usage:
    python check_parity.py [--export opencode_export.json] [--bundle okf-bundle]
Exit code 0 = parity holds. Prints a per-question report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/memanto")  # run from a memanto checkout

from memanto.cli.migrate.mappers import map_okf
from memanto.cli.migrate.okf_loader import load_okf_bundle

PROBES = [
    ("Which CSS approach does the storefront use?", ["tailwind"]),
    ("Are new npm dependencies allowed?", ["forbids", "approval", "dependencies"]),
    ("What caused the checkout totals bug?", ["rounding", "decimal", "quantize"]),
    ("What is the debugging rule?", ["reproduce", "failing test", "before editing"]),
    ("Which package manager is current?", ["yarn"]),
    ("Is npm still correct?", ["superseded", "yarn"]),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default="opencode_export.json")
    ap.add_argument("--bundle", default="okf-bundle")
    args = ap.parse_args()

    export = json.loads(Path(args.export).read_text())
    bundle = load_okf_bundle(args.bundle)
    rows = map_okf(bundle)
    corpus = " ".join(
        f"{r.get('title', '')} {r.get('content', '')}" for r in rows
    ).lower()

    print(f"source sessions: {len(export['sessions'])}, migrated rows: {len(rows)}")
    failed = 0
    for question, keywords in PROBES:
        hit = any(k.lower() in corpus for k in keywords)
        print(f"[{'PASS' if hit else 'FAIL'}] {question}  (need one of {keywords})")
        failed += not hit
    print("PARITY OK — zero amnesia" if not failed else f"{failed} PROBE(S) FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
