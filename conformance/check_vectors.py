#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright 2026 flxk1
"""Check an implementation against the published conformance vectors.

``vectors.json`` is the specification; this runner is one implementation's gate
against it. Any implementation, in any language, conforms if it reproduces every
expectation from the corresponding input.

Usage:
    python3 conformance/check_vectors.py [path-to-vectors.json]

Exit 0 = conformant · 1 = a vector failed · 2 = the suite could not be run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from norm_freshness import (  # noqa: E402
    ChangeKind, RulePin, SourceRef, SourceState, assess,
)


def _pin(d: dict) -> RulePin:
    s = d.get("source")
    return RulePin(d["rule_id"],
                   SourceRef(s["uri"], s["version"], s.get("fragment")) if s else None)


def _state(d: dict) -> SourceState:
    kind = d.get("change_kind")
    return SourceState(d["uri"], d["current_version"], ChangeKind(kind) if kind else None)


def _check(v: dict) -> list[str]:
    report = assess([_pin(p) for p in v["rules"]],
                    {k: _state(s) for k, s in v["observed"].items()})
    by_id = {x.rule_id: x for x in report.verdicts}
    opts = {d.rule_id: list(d.options) for d in report.determinations}
    errs = []
    for rid, want in v["expect"].get("freshness", {}).items():
        got = by_id[rid].freshness.value
        if got != want:
            errs.append(f"freshness[{rid}]: expected {want!r}, got {got!r}")
    for rid, want in v["expect"].get("options", {}).items():
        got = opts.get(rid)
        if got != want:
            errs.append(f"options[{rid}]: expected {want!r}, got {got!r}")
    if "ok" in v["expect"] and report.ok != v["expect"]["ok"]:
        errs.append(f"ok: expected {v['expect']['ok']}, got {report.ok}")
    if "coverage" in v["expect"] and abs(report.coverage - v["expect"]["coverage"]) > 1e-9:
        errs.append(f"coverage: expected {v['expect']['coverage']}, got {report.coverage}")
    return errs


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent / "vectors.json"
    try:
        doc = json.loads(path.read_text())
    except Exception as exc:
        print(f"cannot read vectors: {exc}", file=sys.stderr)
        return 2
    vectors = doc.get("vectors") or []
    if not vectors:
        # Zero vectors passing is the silent-skip failure; refuse rather than report success.
        print("no vectors found — refusing to report conformance", file=sys.stderr)
        return 2

    failed = 0
    for v in vectors:
        try:
            errs = _check(v)
        except Exception as exc:
            errs = [f"<raised {type(exc).__name__}: {exc}>"]
        if errs:
            failed += 1
            print(f"FAIL {v['id']}")
            for e in errs:
                print(f"     {e}")
            print(f"     {v['note']}")
    print(f"{len(vectors) - failed}/{len(vectors)} vectors conformant"
          f"{'' if not failed else f' — {failed} FAILED'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
