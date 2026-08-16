# SPDX-License-Identifier: MIT
# Copyright 2026 flxk1
"""norm-freshness — is the rule you enforce still the rule that was written?

Systems that compile written norms into executable rules monitor the *agent* for
drift and never monitor the *norm*. Statutes are amended, guidance is reissued,
standards land — and a compiled rule has no freshness property, no expiry and no
watcher. It goes on enforcing a superseded text with perfect fidelity, and every
artefact downstream inherits the error while looking immaculate.

This is the missing verdict, in the form a gate can consume at decision time
rather than the form a dashboard shows a human next quarter.

It computes and checks; it does not judge, and it never acts. Four refusals carry
the design — each a place where returning a tidy answer would be inventing one:

* :attr:`Freshness.UNDETERMINED` — the source moved but the *kind* of change is
  unknown. Neither ``CURRENT`` nor ``SUPERSEDED`` is honest, so neither is
  returned. An editorial fix and a repeal are not guessable apart.
* :attr:`Freshness.UNRESOLVABLE` — the source could not be resolved at all.
  Fail-closed: an unanswered question is not a clean bill of health.
* :attr:`Freshness.UNGROUNDED` — the rule cites no source. Enforced anyway,
  reported honestly, and counted against :attr:`FreshnessReport.coverage`.
* **Terminal-for-machine.** Nothing here re-pins, recompiles, disables or halts a
  rule. A rule needing attention yields a :class:`Determination` — the options and
  the evidence, for a person to close. The machine never decides that a legal
  change does not matter.

Closed I/O: this package resolves nothing and reaches no network. You inject the
observed :class:`SourceState` — from an ELI/Akoma Ntoso resolver, a semantic
legislative differ, a vendor feed, or a human. The core is stdlib-only.

Two assumptions the caller owns. Version strings are **opaque and unordered**, so a
difference is read as the source having moved *forward*; a pin ahead of its source
(a bad feed, clock skew) is indistinguishable from ordinary drift. And a
fragment-qualified observation key (``uri#fragment``) takes precedence over the
bare instrument URI where one is supplied.

Grounded in EU AI Act (Reg. 2024/1689) Art. 12 record-keeping and Art. 72
post-market monitoring: a record is interpretable only against the norm actually
in force when it was made.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

__version__ = "0.2.0"

__all__ = [
    "SourceRef",
    "RulePin",
    "ChangeKind",
    "SourceState",
    "Freshness",
    "RuleVerdict",
    "Determination",
    "FreshnessReport",
    "OPTIONS",
    "OPTIONS_BY_CAUSE",
    "assess",
    "assess_rule",
]

#: Default options where the cause is an ordinary supersession.
OPTIONS = ("re-pin", "reassess", "halt")

#: Options per cause. ``re-pin`` is offered **only** where something exists to pin
#: to — never for a repeal (the instrument is gone) and never for an unresolvable
#: source (it was never reached). Offering an impossible option degrades the
#: judgement this module exists to route to a person.
OPTIONS_BY_CAUSE: dict[str, tuple[str, ...]] = {
    "superseded":   ("re-pin", "reassess", "halt"),
    "repealed":     ("retire", "reassess", "halt"),
    "undetermined": ("investigate", "reassess", "halt"),
    "unresolvable": ("retry", "reassess", "halt"),
}


# --------------------------------------------------------------------------- #
# what a rule claims about its source
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class SourceRef:
    """An addressable instrument at a stated version.

    ``uri`` is any stable identifier — an ELI, a CELEX number, a standard's
    designation, an internal document id. This package never dereferences it.
    """

    uri: str
    version: str
    fragment: str | None = None


@dataclass(frozen=True)
class RulePin:
    """One executable rule and the source version it was compiled from.

    ``source`` of ``None`` is a rule that cites nothing — legal, common, and
    reported as :attr:`Freshness.UNGROUNDED` rather than passed over in silence.
    """

    rule_id: str
    source: SourceRef | None = None


# --------------------------------------------------------------------------- #
# what the world says
# --------------------------------------------------------------------------- #

class ChangeKind(str, Enum):
    """How a source moved, in the vocabulary a semantic legislative differ emits.

    ``UNKNOWN`` is first-class: a plain version-string difference tells you
    *that* something changed and nothing about *what*.
    """

    EDITORIAL = "editorial"        # cosmetic / typographical; the norm is unchanged
    AMENDMENT = "amendment"        # substantive change to the text
    COMMENCEMENT = "commencement"  # entry into force / applicability moved
    REPEAL = "repeal"              # the instrument is no longer in force
    UNKNOWN = "unknown"            # it moved; the kind was not determined


#: Change kinds that leave the compiled rule enforceable as written.
_BENIGN = frozenset({ChangeKind.EDITORIAL})
#: Change kinds that require a human determination.
_SUBSTANTIVE = frozenset({ChangeKind.AMENDMENT, ChangeKind.COMMENCEMENT, ChangeKind.REPEAL})


@dataclass(frozen=True)
class SourceState:
    """An observation of a source, injected by the caller.

    ``current_version`` of ``None`` means the source could not be resolved — an
    outage, a dead identifier, an offline run. It does not mean "unchanged".
    """

    uri: str
    current_version: str | None
    change_kind: ChangeKind | None = None
    observed_at: str | None = None


# --------------------------------------------------------------------------- #
# the verdict
# --------------------------------------------------------------------------- #

class Freshness(str, Enum):
    """Per-rule freshness. Deliberately not a total order — see :func:`assess`."""

    CURRENT = "current"
    EDITORIAL_DRIFT = "editorial-drift"
    SUPERSEDED = "superseded"
    UNDETERMINED = "undetermined"
    UNRESOLVABLE = "unresolvable"
    UNGROUNDED = "ungrounded"


def _options_for(freshness: "Freshness", change_kind: ChangeKind | None) -> tuple[str, ...]:
    """Options follow the cause. Never offer an action that cannot be taken."""
    if freshness is Freshness.UNRESOLVABLE:
        return OPTIONS_BY_CAUSE["unresolvable"]
    if freshness is Freshness.UNDETERMINED:
        return OPTIONS_BY_CAUSE["undetermined"]
    if change_kind is ChangeKind.REPEAL:
        return OPTIONS_BY_CAUSE["repealed"]
    return OPTIONS_BY_CAUSE["superseded"]


#: Verdicts that oblige a person to look. Everything else is enforceable as-is.
_NEEDS_HUMAN = frozenset(
    {Freshness.SUPERSEDED, Freshness.UNDETERMINED, Freshness.UNRESOLVABLE}
)


@dataclass(frozen=True)
class RuleVerdict:
    """The freshness of one rule, with the reason stated in words."""

    rule_id: str
    freshness: Freshness
    detail: str = ""
    pinned_version: str | None = None
    current_version: str | None = None
    #: The observed change kind, where one was supplied. Carried so a caller can
    #: tell a repeal from an amendment — both read SUPERSEDED, and they warrant
    #: different responses.
    change_kind: ChangeKind | None = None

    @property
    def requires_determination(self) -> bool:
        return self.freshness in _NEEDS_HUMAN

    @property
    def enforceable(self) -> bool:
        """Whether the rule may still be enforced without a person looking first.

        ``UNGROUNDED`` is enforceable — a rule citing no source makes no claim
        that could have gone stale. It is a coverage problem, not a freshness one.
        """
        return not self.requires_determination


@dataclass(frozen=True)
class Determination:
    """A question put to a person. The machine supplies options, never an answer."""

    rule_id: str
    freshness: Freshness
    detail: str
    options: tuple[str, ...] = OPTIONS


@dataclass(frozen=True)
class FreshnessReport:
    """The verdict over a rule set, and what it obliges.

    :attr:`coverage` is the honest denominator: the share of rules whose source
    was both cited and resolvable. A rule set can be entirely ``CURRENT`` at 12%
    coverage, and that number is the one worth reading.
    """

    verdicts: tuple[RuleVerdict, ...]
    determinations: tuple[Determination, ...]
    resolved: int
    total: int

    @property
    def ok(self) -> bool:
        """True when no rule requires a human determination."""
        return not self.determinations

    @property
    def coverage(self) -> float:
        """Share of rules with a cited, resolvable source. ``0.0`` for an empty set."""
        return self.resolved / self.total if self.total else 0.0

    def by_freshness(self, freshness: Freshness) -> tuple[RuleVerdict, ...]:
        return tuple(v for v in self.verdicts if v.freshness is freshness)


# --------------------------------------------------------------------------- #
# assessment
# --------------------------------------------------------------------------- #

def assess_rule(pin: RulePin, state: SourceState | None) -> RuleVerdict:
    """Assess one rule against one observation. Pure; no I/O, no clock."""
    if pin.source is None:
        return RuleVerdict(pin.rule_id, Freshness.UNGROUNDED, "the rule cites no source")

    pinned = pin.source.version
    if state is None:
        return RuleVerdict(
            pin.rule_id,
            Freshness.UNRESOLVABLE,
            f"no observation supplied for {pin.source.uri}",
            pinned,
            None,
        )
    if state.current_version is None:
        return RuleVerdict(
            pin.rule_id,
            Freshness.UNRESOLVABLE,
            f"{state.uri} could not be resolved; unresolved is not unchanged",
            pinned,
            None,
        )
    if state.current_version == pinned:
        return RuleVerdict(pin.rule_id, Freshness.CURRENT, "", pinned, state.current_version)

    # It moved. What kind of move decides everything, and guessing is not allowed.
    kind = state.change_kind
    if kind is None or kind is ChangeKind.UNKNOWN:
        return RuleVerdict(
            pin.rule_id,
            Freshness.UNDETERMINED,
            f"{state.uri} moved {pinned} → {state.current_version}; change kind not determined",
            pinned,
            state.current_version,
        )
    if kind in _BENIGN:
        return RuleVerdict(
            pin.rule_id,
            Freshness.EDITORIAL_DRIFT,
            f"{state.uri} moved {pinned} → {state.current_version} ({kind.value}); text unchanged in substance",
            pinned,
            state.current_version,
        )
    if kind in _SUBSTANTIVE:
        return RuleVerdict(
            pin.rule_id,
            Freshness.SUPERSEDED,
            f"{state.uri} moved {pinned} → {state.current_version} ({kind.value})",
            pinned,
            state.current_version,
            kind,
        )
    # An unrecognised kind is an unknown kind, and unknown means undetermined.
    return RuleVerdict(
        pin.rule_id,
        Freshness.UNDETERMINED,
        f"{state.uri} moved {pinned} → {state.current_version}; unrecognised change kind {kind!r}",
        pinned,
        state.current_version,
    )


def assess(
    pins: Iterable[RulePin],
    observed: Mapping[str, SourceState] | None = None,
) -> FreshnessReport:
    """Assess a rule set against observed source states, keyed by source URI.

    A pin whose URI is absent from ``observed`` is ``UNRESOLVABLE``, not
    ``CURRENT``: the caller not having looked is not evidence that nothing moved.

    Returns the verdicts, the determinations they oblige, and the coverage. No
    total order over verdicts is offered and no single "freshest" answer is
    computed — a rule set is not one rule.
    """
    lookup = dict(observed or {})
    verdicts: list[RuleVerdict] = []
    determinations: list[Determination] = []
    resolved = 0

    for pin in pins:
        state = None
        if pin.source is not None:
            # A fragment-qualified observation is more specific and wins; the bare
            # instrument URI is the fallback. Previously a fragment-keyed entry was
            # silently ignored, letting a caller believe they had supplied
            # per-article data when they had not.
            if pin.source.fragment:
                state = lookup.get(f"{pin.source.uri}#{pin.source.fragment}")
            if state is None:
                state = lookup.get(pin.source.uri)
        verdict = assess_rule(pin, state)
        verdicts.append(verdict)
        if verdict.freshness in (Freshness.CURRENT, Freshness.EDITORIAL_DRIFT, Freshness.SUPERSEDED):
            resolved += 1
        if verdict.requires_determination:
            determinations.append(Determination(
                verdict.rule_id, verdict.freshness, verdict.detail,
                _options_for(verdict.freshness, verdict.change_kind),
            ))

    return FreshnessReport(tuple(verdicts), tuple(determinations), resolved, len(verdicts))
