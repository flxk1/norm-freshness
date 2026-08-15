# norm-freshness

Systems that compile written norms into executable rules watch the *agent* for drift. None of them
watch the *norm*. Statutes get amended, guidance is reissued, standards land — and a compiled rule
has no freshness property, no expiry, and no watcher. It goes on enforcing a superseded text with
perfect fidelity, and every artefact downstream inherits the error while looking immaculate.

This is the missing verdict, in the form **a gate can consume at decision time** rather than the
form a dashboard shows someone next quarter.

It computes and checks; it does not judge, and **it never acts.**

## The four refusals

Each is a place where returning a tidy answer would be inventing one.

| | |
|---|---|
| **UNDETERMINED** | The source moved but the *kind* of change is unknown. An editorial fix and a repeal are not guessable apart, so neither `CURRENT` nor `SUPERSEDED` is returned. A bare version difference is not a fact about the norm. |
| **UNRESOLVABLE** | The source could not be resolved — an outage, a dead identifier, an offline run. **Fail-closed:** an unanswered question is not a clean bill of health, and a pin you never looked up is not `CURRENT`. |
| **UNGROUNDED** | The rule cites no source at all. Still enforceable — it makes no claim that could have gone stale — but reported, and counted against `coverage`. |
| **Terminal-for-machine** | Nothing here re-pins, recompiles, disables or halts. A rule needing attention yields a `Determination` — the options and the evidence, for a person to close. **The machine never decides that a legal change does not matter.** |

## Install

```bash
pip install .
```

Stdlib-only, no runtime dependencies. Tests need `pytest` (`pip install ".[test]"`).

## Usage

```python
from norm_freshness import (
    RulePin, SourceRef, SourceState, ChangeKind, Freshness, assess,
)

AI_ACT = "http://data.europa.eu/eli/reg/2024/1689/oj"
STANDARD = "urn:iso:std:iso-iec:42001"

rules = [
    RulePin("gate.human-oversight", SourceRef(AI_ACT, "2024-07-12", "art_14")),
    RulePin("gate.record-keeping",  SourceRef(AI_ACT, "2024-07-12", "art_12")),
    RulePin("gate.mgmt-system",     SourceRef(STANDARD, "2023")),
    RulePin("gate.house-style"),                      # cites nothing — legal, and reported
]

# You supply the observations: from an ELI/Akoma Ntoso resolver, a semantic
# legislative differ, a vendor feed, or a person. This package resolves nothing.
observed = {
    AI_ACT:   SourceState(AI_ACT, "2024-11-20", ChangeKind.EDITORIAL),  # a corrigendum
    STANDARD: SourceState(STANDARD, None),                             # registry unreachable
}

report = assess(rules, observed)

print("enforceable without review:", report.ok)
print("coverage:", report.coverage)
for verdict in report.verdicts:
    print(f"  {verdict.rule_id:24} {verdict.freshness.value}")
for determination in report.determinations:
    print("needs a person:", determination.rule_id, "->", determination.options)
```

Output (behaviour proven by the test suite):

```
enforceable without review: False
coverage: 0.5
  gate.human-oversight     editorial-drift
  gate.record-keeping      editorial-drift
  gate.mgmt-system         unresolvable
  gate.house-style         ungrounded
needs a person: gate.mgmt-system -> ('re-pin', 'reassess', 'halt')
```

Three things in that output are the whole point. The corrigendum did **not** stop the two AI Act
rules — an editorial change is drift, not supersession, and a checker that halted on it would be
turned off within a week. The unreachable registry did **not** silently pass as current. And
`coverage: 0.5` is the number worth reading: a rule set can be entirely `CURRENT` at 12% coverage,
which tells you the freshness verdict is answering a much smaller question than it appears to.

## What you get back

`assess` returns per-rule `RuleVerdict`s, the `Determination`s they oblige, and the coverage —
and deliberately offers **no single "freshest" answer** for the set. A rule set is not one rule,
and collapsing it would hide exactly the rule you needed to see.

## Limitations

- **It resolves nothing.** No network, no clock, no identifier dereferencing. You inject
  `SourceState`; where that observation comes from, and how good it is, is yours (closed I/O).
- **Change-kind grading is only as good as your differ.** If your source of truth cannot tell an
  amendment from a corrigendum, every move lands as `UNDETERMINED` — which is the honest outcome,
  not a defect, but it means the value of this package tracks the quality of the differ behind it.
- **Fragment-level precision is not checked.** A pin may name an article, but freshness is assessed
  at the version of the instrument. An amendment elsewhere in the same instrument will flag a rule
  whose own article did not move. Conservative, and noisy in proportion to instrument size.
- **It does not interpret.** Whether a superseded rule is still *substantially* correct is a legal
  judgement this package exists to route to a person, never to make.
- **It models one of two staleness clocks.** This answers whether the *norm* has moved. It says
  nothing about the **distribution** clock — how long since your engine last successfully
  reconciled with its own policy source. Those are independent: an engine serving a cached policy
  bundle after an outage is fully current on the norm and hours stale on distribution, and the
  reverse is equally possible. A verdict that carries neither age looks identical to a fresh one.
  Bound both, or you have measured the clock that was easier to reach.

## Origin & prior art

Composed, not reinvented. Legal versioning and change detection are owned upstream: the
**European Legislation Identifier (ELI)** and **Akoma Ntoso / LegalDocML** carry versioned identity
and amendment history, platforms like **Indigo** track amended versions, and semantic legislative
differs already classify a change as amendment vs commencement vs cosmetic fix. Regulatory-change
monitoring is a mature commercial category (**OSCAL**-native GRC platforms and the RegTech feeds),
producing alerts and remediation workflows for people.

What none of them produce — and what this package owns — is the **enforcement-time verdict**: a
machine-readable freshness state for *one executable rule* against the source version it was
compiled from, fail-closed on unresolvable, refusing to classify an unexplained move, reporting its
own coverage, and terminal-for-machine so that no code path lets a system conclude by itself that a
legal change was immaterial. GRC tells a compliance team the law moved. This tells a gate whether
the rule in front of it may still fire.

Grounded in EU AI Act (Reg. 2024/1689) Art. 12 (record-keeping) and Art. 72 (post-market
monitoring): a record is interpretable only against the norm actually in force when it was made.

```
PRIOR-ART:
  incumbent(s):      ELI · Akoma Ntoso / LegalDocML · Indigo (amended-version tracking) ·
                     semantic legislative differs · OSCAL + GRC regulatory-change platforms
  distinctive layer: the enforcement-time freshness verdict for a compiled rule — graded by
                     change kind, UNDETERMINED rather than a guess, UNRESOLVABLE fail-closed,
                     coverage as the honest denominator, terminal-for-machine (determinations,
                     never actions)
  decision:          build-distinctive (consumes the incumbents' identifiers and diffs; owns the
                     verdict a gate can act on)
```

## License

MIT. See `LICENSE`. Copyright 2026 flxk1.
