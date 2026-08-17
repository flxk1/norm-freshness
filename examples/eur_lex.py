# SPDX-License-Identifier: MIT
"""Assess rules pinned to a real EU instrument, using what EUR-Lex actually publishes.

A universality test. Until now the only inputs this package had seen were its
author's fixtures. The facts below were read off the live EUR-Lex record for
Regulation (EU) 2024/1689 (the AI Act) on 2026-08-17:

    ELI            http://data.europa.eu/eli/reg/2024/1689/oj
    CELEX          32024R1689
    consolidations 12/07/2024 (original) and 27/07/2026 (current)
    status         "In force" — "This act has been changed"

Three things the exercise shows, in order of how much they matter.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from norm_freshness import RulePin, SourceRef, SourceState, ChangeKind, assess

ELI = "http://data.europa.eu/eli/reg/2024/1689/oj"
CURRENT_CONSOLIDATION = "2026-07-27"
CELEX = "32024R1689"

print("1. A rule pinned at publication, against the live record")
report = assess(
    [RulePin("gate.human-oversight", SourceRef(ELI, "2024-07-12", "art_14"))],
    # EUR-Lex tells you the consolidation moved. It does not tell you what KIND
    # of change it was — that needs the amending acts read, or a semantic differ.
    {ELI: SourceState(ELI, CURRENT_CONSOLIDATION, change_kind=None)},
)
v = report.verdicts[0]
print(f"   {v.freshness.value}  ->  {report.determinations[0].options}")
print("   Correct, and the practical ceiling: with no differ, EUR-Lex alone can")
print("   never yield EDITORIAL_DRIFT or SUPERSEDED. Every moved instrument is")
print("   UNDETERMINED, and the graded verdicts are unreachable from this source.\n")

print("2. The same rule, once a differ supplies the change kind")
report = assess(
    [RulePin("gate.human-oversight", SourceRef(ELI, "2024-07-12", "art_14"))],
    {ELI: SourceState(ELI, CURRENT_CONSOLIDATION, ChangeKind.AMENDMENT)},
)
v = report.verdicts[0]
print(f"   {v.freshness.value}  ->  {report.determinations[0].options}\n")

print("3. The footgun: pinning an identifier that never moves")
report = assess(
    [RulePin("gate.human-oversight", SourceRef(ELI, CELEX, "art_14"))],
    # A CELEX number identifies the ACT, not a version of it. It is unchanged by
    # consolidation, so a feed reporting it back reads as CURRENT forever.
    {ELI: SourceState(ELI, CELEX, change_kind=None)},
)
print(f"   {report.verdicts[0].freshness.value}  (ok={report.ok})")
print("   The act has been amended and this reports CURRENT. Version strings are")
print("   opaque to this package: it cannot tell a version from a permalink.")
print("   Pin the consolidation date. Never pin CELEX, and never pin the ELI.")
