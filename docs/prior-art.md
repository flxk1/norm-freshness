# Prior art and related

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
