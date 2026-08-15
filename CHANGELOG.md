# Changelog

## 0.1.0 — 2026-08-15

Initial draft. The norm-freshness verdict: per-rule staleness for compiled rules pinned to a
versioned source, graded by *change kind* (editorial drift vs amendment / commencement / repeal)
rather than by a bare version difference. Four refusals — `UNDETERMINED` when the kind of change
is unknown, `UNRESOLVABLE` when the source could not be resolved (fail-closed), `UNGROUNDED` for a
rule citing no source, and terminal-for-machine throughout: a flagged rule yields a
`Determination` with options, never an action. Reports coverage as the honest denominator.
Stdlib-only; source observations are injected, nothing is dereferenced.
