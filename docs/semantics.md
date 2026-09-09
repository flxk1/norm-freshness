# Semantics and limitations

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
- **Change-kind grading is only as good as your differ, and the ceiling is low without one.**
  EUR-Lex publishes consolidation dates and an "this act has been changed" flag; it does not
  publish the *kind* of change. So against the primary EU legal source, unaided, every moved
  instrument lands as `UNDETERMINED` and the graded verdicts — `EDITORIAL_DRIFT`, `SUPERSEDED` —
  are unreachable. Honest, and a real limit on utility. Measured in `examples/eur_lex.py`.
- **`version` must change when the instrument changes.** A consolidation date qualifies; a
  permalink does not. CELEX, ELI and DOI identify the *act*, not a version of it, and survive
  amendment untouched — pin one and the assessment reads `CURRENT` for ever. The package cannot
  detect this: version strings are opaque to it by design.
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
