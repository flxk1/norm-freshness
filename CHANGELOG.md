# Changelog

## 0.3.0 — 2026-08-17

No behaviour change; two limitations documented that only appeared when the package was pointed at
a real legal source instead of its author's fixtures.

`examples/eur_lex.py` assesses rules against the live EUR-Lex record for Regulation (EU) 2024/1689.
It consumed it unmodified, and exposed:

- **A ceiling.** EUR-Lex publishes consolidation dates and a "this act has been changed" flag, not
  the *kind* of change. Unaided, every moved instrument lands as `UNDETERMINED` and the graded
  verdicts are unreachable from that source alone.
- **A footgun, now a stated contract.** `SourceRef.version` must be a value that CHANGES when the
  instrument changes. A permalink — CELEX, ELI, DOI — identifies the act rather than a version of
  it and survives amendment untouched; pin one and the assessment reads `CURRENT` for ever. The
  package cannot detect this, since version strings are opaque to it by design.

## 0.2.0 — 2026-08-16

Found by using the package as a consumer would rather than by testing it against its own
assumptions.

- **Options now follow the cause.** `re-pin` was offered for every determination, including a
  **repeal** (the instrument is gone) and an **unresolvable** source (it was never reached) — an
  action that cannot be taken. Repeal offers `retire`, unresolvable offers `retry`, undetermined
  offers `investigate`. In a terminal-for-machine design the options *are* the product; an
  impossible one degrades the judgement it exists to route to a person.
- **`RuleVerdict.change_kind`** carries the cause, since a repeal and an amendment both read
  `SUPERSEDED` and warrant different responses.
- **Fragment-keyed observations are honoured.** An observation keyed `uri#fragment` now takes
  precedence over the instrument-level one, falling back to the bare URI. Previously such a key
  was accepted and **silently ignored**, letting a caller believe they had supplied per-article
  data when they had not.
- Documented an assumption the caller owns: version strings are opaque and unordered, so a pin
  ahead of its source is indistinguishable from ordinary drift.

Back-compatible: `OPTIONS` is unchanged and still the amendment case.

## 0.1.0 — 2026-08-15

Initial draft. The norm-freshness verdict: per-rule staleness for compiled rules pinned to a
versioned source, graded by *change kind* (editorial drift vs amendment / commencement / repeal)
rather than by a bare version difference. Four refusals — `UNDETERMINED` when the kind of change
is unknown, `UNRESOLVABLE` when the source could not be resolved (fail-closed), `UNGROUNDED` for a
rule citing no source, and terminal-for-machine throughout: a flagged rule yields a
`Determination` with options, never an action. Reports coverage as the honest denominator.
Stdlib-only; source observations are injected, nothing is dereferenced.
