# Usage and verdicts


Per-rule staleness for compiled rules pinned to a versioned source. Answers, at decision time,
whether the rule a gate is about to apply still matches the text it was compiled from.

Systems that compile written norms into executable rules monitor the agent for drift. They do not
monitor the norm. A compiled rule has no freshness property and no expiry, so it continues
enforcing a superseded text without signalling anything.

## Install

```bash
pip install "git+https://github.com/flxk1/norm-freshness"
```

No runtime dependencies.

Distributed from this repository; there is no package-index release. Tests:
`pip install ".[test]"` from a clone.

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
