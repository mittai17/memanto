"""Recall-parity harness: prove zero amnesia after the migration round-trip.

1. Loads the source export (questions we expect the memory to answer).
2. Loads the generated OKF bundle with Memanto's own ``load_okf_bundle``.
3. Maps it with ``mappers.map_okf`` (same code path as ``migrate okf``).
4. Re-runs the adapter's ``convert`` on the export and asserts the row
   count matches (no dropped memories).
5. Asserts every probe question is answerable from a SINGLE migrated row
   (per-row matching — a combined-corpus match could hide dropped rows).

Usage:
    python check_parity.py [--export opencode_export.json] [--bundle okf-bundle]
Exit code 0 = parity holds. Prints a per-question report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from memanto.cli.migrate.mappers import map_okf
from memanto.cli.migrate.okf_loader import load_okf_bundle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opencode_to_okf import convert

# (question, keywords, expected OKF type of the answering row)
PROBES = [
    ("Which CSS approach does the storefront use?", ["tailwind"], "learning"),
    ("Are new npm dependencies allowed?", ["forbids", "approval"], "learning"),
    ("What caused the checkout totals bug?", ["rounding", "quantize"], "learning"),
    ("What is the debugging rule?", ["reproduce", "before editing"], "learning"),
    ("Which package manager is current?", ["yarn"], "decision"),
    ("Is the npm instruction still valid?", ["superseded"], "decision"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default="opencode_export.json")
    ap.add_argument("--bundle", default="okf-bundle")
    args = ap.parse_args()

    export = json.loads(Path(args.export).read_text())
    bundle = load_okf_bundle(args.bundle)
    rows = map_okf(bundle)
    expected = convert(export)

    print(f"source sessions: {len(export['sessions'])}, "
          f"adapter memories: {len(expected)}, migrated rows: {len(rows)}")
    failed = 0
    if len(rows) != len(expected):
        print(f"[FAIL] row count {len(rows)} != adapter output {len(expected)}: rows dropped")
        failed += 1
    else:
        print("[PASS] row count matches adapter output — nothing dropped")

    row_texts = [(r.get("type"), f"{r.get('title', '')} {r.get('content', '')}".lower())
                 for r in rows]
    for question, keywords, want_type in PROBES:
        hit = any(
            rtype == want_type and any(k.lower() in text for k in keywords)
            for rtype, text in row_texts
        )
        print(f"[{'PASS' if hit else 'FAIL'}] {question}  (single {want_type} row, {keywords})")
        failed += not hit
    print("PARITY OK — zero amnesia" if not failed else f"{failed} PROBE(S) FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
