# norm-freshness

Per-rule staleness for compiled rules pinned to a versioned source. Answers, at decision time,
whether the rule a gate is about to apply still matches the text it was compiled from.

Systems that compile written norms into executable rules monitor the agent for drift. They do not
monitor the norm. A compiled rule has no freshness property and no expiry, so it continues
enforcing a superseded text without signalling anything.

## Install

```bash
pip install .
```

No runtime dependencies. Tests: `pip install ".[test]"`.

## Usage

```python
from norm_freshness import RulePin, SourceRef, SourceState, ChangeKind, assess

AI_ACT = "http://data.europa.eu/eli/reg/2024/1689/oj"
STANDARD = "urn:iso:std:iso-iec:42001"

rules = [
    RulePin("gate.human-oversight", SourceRef(AI_ACT, "2024-07-12", "art_14")),
    RulePin("gate.record-keeping",  SourceRef(AI_ACT, "2024-07-12", "art_12")),
    RulePin("gate.mgmt-system",     SourceRef(STANDARD, "2023")),
    RulePin("gate.house-style"),                       # cites no source
]

# Observations are injected — from an ELI/Akoma Ntoso resolver, a legislative
# differ, a vendor feed, or a person. This package resolves nothing.
observed = {
    AI_ACT:   SourceState(AI_ACT, "2024-11-20", ChangeKind.EDITORIAL),
    STANDARD: SourceState(STANDARD, None),             # unreachable
}

report = assess(rules, observed)
print(report.ok, report.coverage)
for v in report.verdicts:
    print(f"  {v.rule_id:24} {v.freshness.value}")
for d in report.determinations:
    print(" ", d.rule_id, d.options)
```

```
False 0.5
  gate.human-oversight     editorial-drift
  gate.record-keeping      editorial-drift
  gate.mgmt-system         unresolvable
  gate.house-style         ungrounded
  gate.mgmt-system ('retry', 'reassess', 'halt')
```

## Verdicts

| `Freshness` | meaning | enforceable |
|---|---|---|
| `CURRENT` | pinned version matches the source | yes |
| `EDITORIAL_DRIFT` | source moved; change kind was editorial | yes |
| `SUPERSEDED` | source moved by amendment, commencement or repeal | no |
| `UNDETERMINED` | source moved, change kind unknown | no |
| `UNRESOLVABLE` | source could not be resolved | no |
| `UNGROUNDED` | the rule cites no source | yes |

`coverage` is the share of rules with a cited, resolvable source. A rule set can be entirely
`CURRENT` at low coverage; the figure states how small a question the verdict answered.

## Semantics

- **Graded by change kind, not by version difference.** An editorial corrigendum is drift and does
  not stop enforcement. A checker that halted on typo fixes would be switched off.
- **`UNDETERMINED` rather than a guess.** A bare version difference does not distinguish a
  corrigendum from a repeal, so neither `CURRENT` nor `SUPERSEDED` is returned.
- **`UNRESOLVABLE` is fail-closed.** An unreachable registry, and a pin never looked up, are not
  `CURRENT`. A URI absent from `observed` is `UNRESOLVABLE`, not assumed unchanged.
- **`UNGROUNDED` is enforceable.** A rule citing no source makes no claim that could go stale. It
  counts against `coverage`, not against the rule.
- **Terminal-for-machine.** Nothing re-pins, recompiles, disables or halts. A flagged rule yields a
  `Determination` carrying options for a person to close.
- **Options follow the cause** (0.2.0). `re-pin` is offered only where something exists to pin to.

  | cause | options |
  |---|---|
  | amendment / commencement | `re-pin` · `reassess` · `halt` |
  | repeal | `retire` · `reassess` · `halt` — the instrument is gone |
  | undetermined | `investigate` · `reassess` · `halt` — re-pinning before knowing what changed is premature |
  | unresolvable | `retry` · `reassess` · `halt` — the source was never reached |

  `RuleVerdict.change_kind` carries the cause, since a repeal and an amendment both read
  `SUPERSEDED`.
- `assess` returns per-rule verdicts and no aggregate freshness. A rule set is not one rule.
- No clock, no network, no identifier dereferencing.

## Limitations

- **It resolves nothing.** `SourceState` is yours to supply; its quality bounds everything here.
- **Change-kind grading is only as good as your differ.** Without one, every move lands as
  `UNDETERMINED` — honest, but less useful.
- **Fragment-level precision depends on your observations.** Supply an observation keyed
  `uri#fragment` and it takes precedence over the instrument-level one; supply only the bare URI
  and freshness is assessed at instrument version, so an amendment elsewhere in the same
  instrument flags a rule whose article did not move. *(Before 0.2.0 a fragment-keyed observation
  was accepted and silently ignored.)*
- **Version strings are opaque and unordered.** A difference is read as the source having moved
  *forward*. A pin **ahead** of its source — a bad feed, clock skew — is indistinguishable from
  ordinary drift and will be reported as such.
- **It models one of two staleness clocks.** This is the *norm* clock. It says nothing about the
  *distribution* clock — how long since your engine last reconciled with its own policy source. An
  engine serving a cached bundle after an outage is current on the first and stale on the second.
- It does not interpret. Whether a superseded rule remains substantially correct is a legal
  judgement for a person.

## Prior art

Legal versioning and change detection are owned upstream: **ELI**, **Akoma Ntoso / LegalDocML**,
amended-version tracking (Indigo), and semantic legislative differs that classify a change as
amendment, commencement or cosmetic. Regulatory-change monitoring is a mature commercial category
(**OSCAL**-native GRC platforms, RegTech feeds) producing alerts and workflows for people.

What those do not produce is a machine-readable freshness state for one executable rule, at
decision time, fail-closed on unresolvable and terminal-for-machine. GRC tells a compliance team
the law moved; this tells a gate whether the rule in front of it may still fire.

```
PRIOR-ART:
  incumbent(s):      ELI · Akoma Ntoso / LegalDocML · Indigo · semantic legislative differs ·
                     OSCAL + GRC regulatory-change platforms
  distinctive layer: the enforcement-time freshness verdict for a compiled rule — graded by
                     change kind, UNDETERMINED rather than a guess, UNRESOLVABLE fail-closed,
                     coverage as denominator, terminal-for-machine
  decision:          build-distinctive (consumes the incumbents' identifiers and diffs)
```

Relevant to EU AI Act (Reg. 2024/1689) Arts. 12 and 72.

## Related

One of four narrow governance primitives, each usable alone:

- [`enforcement-posture`](https://github.com/flxk1/enforcement-posture) — binds evidence to the
  controls that were in force while it was recorded
- [`norm-freshness`](https://github.com/flxk1/norm-freshness) — whether the rule a gate applies
  still matches the text it was compiled from
- [`effect-reconciliation`](https://github.com/flxk1/effect-reconciliation) — permissions granted
  against effects observed
- [`oversight-certificate`](https://github.com/flxk1/oversight-certificate) — re-checkable proof
  that a qualified human decided

They answer different questions about the same decision: *who decided* (oversight-certificate),
*under what regime* (enforcement-posture), *against which version of the rule* (norm-freshness),
and *did the permission produce the effect* (effect-reconciliation).

## License

MIT. See `LICENSE`. Copyright 2026 flxk1.
