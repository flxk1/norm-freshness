# Against a real source

## Against a real source

`examples/eur_lex.py` assesses rules pinned to Regulation (EU) 2024/1689 using what EUR-Lex
actually publishes — read off the live record on 2026-08-17, where the act carries two
consolidations (12/07/2024 and 27/07/2026) and the status "This act has been changed".

The package consumed it unmodified. The run surfaced the two limitations in
[semantics.md](semantics.md#limitations): the
`UNDETERMINED` ceiling without a differ, and the permalink footgun, where pinning CELEX
`32024R1689` reports `CURRENT` against an act that has in fact been amended.
