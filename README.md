# norm-freshness

Per-rule freshness verdict for compiled rules pinned to a versioned source, computed at decision time from injected observations of that source.

## Problem

The rule in force is the rule as compiled months ago. Per-rule freshness verdict against the versioned source, fail-closed.

## Install

`pip install "git+https://github.com/flxk1/norm-freshness"`

## Usage

```python
rules = [RulePin("gate.human-oversight", SourceRef(AI_ACT, "2024-07-12", "art_14"))]
observed = {AI_ACT: SourceState(AI_ACT, "2024-11-20", ChangeKind.EDITORIAL)}
assess(rules, observed).verdicts[0].freshness.value   # editorial-drift
```

## Example

```
in : assess([RulePin("gate.erasure", SourceRef("eli/reg/2016/679", "2016-05-04", "art_17"))],
            {"eli/reg/2016/679": SourceState("eli/reg/2016/679", "2027-01-01", ChangeKind.EDITORIAL)}).verdicts[0]
out: Freshness.EDITORIAL_DRIFT
     eli/reg/2016/679 moved 2016-05-04 → 2027-01-01 (editorial); text unchanged in substance
```

## Interface

- `RulePin(rule_id, source=None)` with `SourceRef(uri, version, fragment=None)`
- `SourceState(uri, current_version, change_kind=None, observed_at=None)`, keyed by `uri` or `uri#fragment`
- `assess(pins, observed) -> FreshnessReport(ok, coverage, verdicts, determinations)`
- `Freshness`: CURRENT, EDITORIAL_DRIFT, UNGROUNDED (enforceable); SUPERSEDED, UNDETERMINED, UNRESOLVABLE (fail-closed)
- `Determination.options` by cause: re-pin, retire, investigate, retry, plus reassess, halt

## Family

Assurance artifact, pillar "source validity" of [governance-certification](https://github.com/flxk1/governance-certification). Consumes: source identifiers and change observations (ELI, Akoma Ntoso, legislative differs; `examples/eur_lex.py` against EUR-Lex); resolves nothing itself. Docs: [docs/](docs/).

## Status

0.3.0 · 30 tests · 14 conformance vectors · Python ≥ 3.10

## How this is made

The code and documentation are written with Loomground agents running on Claude (Anthropic). The maintainer reads and corrects all of it.

## License

MIT — [LICENSES/MIT.txt](LICENSES/MIT.txt)
