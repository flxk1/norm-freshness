# SPDX-License-Identifier: MIT
# Copyright 2026 flxk1
"""Tests for norm_freshness. Runs under both `pytest` and
`python -m unittest discover -s tests`.

Pure functions over injected observations — no network, no clock, no fixtures
beyond plain data. Every refusal (UNDETERMINED / UNRESOLVABLE / UNGROUNDED) and
the terminal-for-machine contract are pinned here."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from norm_freshness import (  # noqa: E402
    OPTIONS,
    OPTIONS_BY_CAUSE,
    ChangeKind,
    Determination,
    Freshness,
    RulePin,
    SourceRef,
    SourceState,
    assess,
    assess_rule,
)

AI_ACT = "http://data.europa.eu/eli/reg/2024/1689/oj"


def pin(rule_id="rule-1", uri=AI_ACT, version="2024-07-12", fragment=None):
    return RulePin(rule_id, SourceRef(uri, version, fragment))


def state(uri=AI_ACT, current="2024-07-12", kind=None):
    return SourceState(uri, current, kind)


class TestUnchanged(unittest.TestCase):
    def test_same_version_is_current(self):
        verdict = assess_rule(pin(), state())
        self.assertIs(verdict.freshness, Freshness.CURRENT)
        self.assertTrue(verdict.enforceable)
        self.assertFalse(verdict.requires_determination)


class TestGradedByChangeKind(unittest.TestCase):
    """A version bump is not a fact about the norm until you know what kind it was."""

    def test_editorial_change_is_drift_not_supersession(self):
        verdict = assess_rule(pin(), state(current="2024-11-01", kind=ChangeKind.EDITORIAL))
        self.assertIs(verdict.freshness, Freshness.EDITORIAL_DRIFT)
        self.assertTrue(verdict.enforceable, "a typo fix must not stop enforcement")
        self.assertFalse(verdict.requires_determination)

    def test_substantive_changes_supersede(self):
        for kind in (ChangeKind.AMENDMENT, ChangeKind.COMMENCEMENT, ChangeKind.REPEAL):
            with self.subTest(kind=kind):
                verdict = assess_rule(pin(), state(current="2025-01-01", kind=kind))
                self.assertIs(verdict.freshness, Freshness.SUPERSEDED)
                self.assertFalse(verdict.enforceable)
                self.assertTrue(verdict.requires_determination)

    def test_the_verdict_carries_both_versions(self):
        verdict = assess_rule(pin(version="a"), state(current="b", kind=ChangeKind.AMENDMENT))
        self.assertEqual(verdict.pinned_version, "a")
        self.assertEqual(verdict.current_version, "b")


class TestRefusals(unittest.TestCase):
    """The four places a tidy answer would be an invented one."""

    def test_unknown_change_kind_is_undetermined_never_current(self):
        verdict = assess_rule(pin(), state(current="2025-01-01", kind=ChangeKind.UNKNOWN))
        self.assertIs(verdict.freshness, Freshness.UNDETERMINED)
        self.assertNotIn(verdict.freshness, (Freshness.CURRENT, Freshness.SUPERSEDED))

    def test_absent_change_kind_is_undetermined_never_superseded(self):
        """A bare version difference does not license a supersession claim either."""
        verdict = assess_rule(pin(), state(current="2025-01-01", kind=None))
        self.assertIs(verdict.freshness, Freshness.UNDETERMINED)
        self.assertTrue(verdict.requires_determination)

    def test_an_unrecognised_change_kind_degrades_to_undetermined(self):
        rogue = SourceState(AI_ACT, "2025-01-01", "consolidation")  # not a ChangeKind member
        self.assertIs(assess_rule(pin(), rogue).freshness, Freshness.UNDETERMINED)

    def test_unresolved_source_is_unresolvable_not_current(self):
        verdict = assess_rule(pin(), SourceState(AI_ACT, None))
        self.assertIs(verdict.freshness, Freshness.UNRESOLVABLE)
        self.assertFalse(verdict.enforceable, "an unanswered question is not a clean bill of health")

    def test_missing_observation_is_unresolvable_not_current(self):
        self.assertIs(assess_rule(pin(), None).freshness, Freshness.UNRESOLVABLE)

    def test_a_rule_citing_no_source_is_ungrounded(self):
        verdict = assess_rule(RulePin("rule-x", None), None)
        self.assertIs(verdict.freshness, Freshness.UNGROUNDED)

    def test_ungrounded_is_enforceable_but_counts_against_coverage(self):
        """It makes no claim that could have gone stale — it is a coverage problem."""
        report = assess([RulePin("rule-x", None)])
        self.assertTrue(report.verdicts[0].enforceable)
        self.assertTrue(report.ok)
        self.assertEqual(report.coverage, 0.0)


class TestTerminalForMachine(unittest.TestCase):
    """The module surfaces determinations; it never closes one."""

    def test_each_flagged_rule_yields_a_determination_with_options(self):
        report = assess([pin()], {AI_ACT: state(current="2025-01-01", kind=ChangeKind.AMENDMENT)})
        self.assertEqual(len(report.determinations), 1)
        determination = report.determinations[0]
        self.assertIsInstance(determination, Determination)
        self.assertEqual(determination.options, OPTIONS)
        self.assertEqual(determination.options, ("re-pin", "reassess", "halt"))

    def test_enforceable_verdicts_raise_no_determination(self):
        report = assess([pin()], {AI_ACT: state(kind=ChangeKind.EDITORIAL)})
        self.assertEqual(report.determinations, ())
        self.assertTrue(report.ok)

    def test_the_package_exposes_no_way_to_act_on_a_rule(self):
        """No re-pin, recompile, disable or halt anywhere in the public surface."""
        import norm_freshness

        forbidden = ("repin", "re_pin", "recompile", "disable", "halt", "apply", "update", "fix")
        offenders = [
            name
            for name in norm_freshness.__all__
            if any(word in name.lower() for word in forbidden)
        ]
        self.assertEqual(offenders, [], "the machine must not offer to decide")


class TestReportOverASet(unittest.TestCase):
    def test_coverage_is_the_honest_denominator(self):
        """All-CURRENT at low coverage is the number worth reading."""
        pins = [
            pin("a"),
            pin("b", uri="urn:other", version="1"),
            RulePin("c", None),
            RulePin("d", None),
        ]
        report = assess(pins, {AI_ACT: state(), "urn:other": SourceState("urn:other", None)})
        self.assertEqual(report.resolved, 1)
        self.assertEqual(report.total, 4)
        self.assertEqual(report.coverage, 0.25)
        self.assertIs(report.by_freshness(Freshness.CURRENT)[0].freshness, Freshness.CURRENT)
        self.assertEqual(len(report.by_freshness(Freshness.UNGROUNDED)), 2)

    def test_a_pin_absent_from_observations_is_unresolvable(self):
        report = assess([pin()], {})
        self.assertIs(report.verdicts[0].freshness, Freshness.UNRESOLVABLE)
        self.assertFalse(report.ok)

    def test_one_stale_rule_makes_the_set_not_ok_without_hiding_the_rest(self):
        pins = [pin("fresh"), pin("stale", uri="urn:x", version="1")]
        observed = {
            AI_ACT: state(),
            "urn:x": SourceState("urn:x", "2", ChangeKind.REPEAL),
        }
        report = assess(pins, observed)
        self.assertFalse(report.ok)
        self.assertEqual(len(report.determinations), 1)
        self.assertEqual(report.determinations[0].rule_id, "stale")
        still_current = report.by_freshness(Freshness.CURRENT)
        self.assertEqual([v.rule_id for v in still_current], ["fresh"])
        self.assertTrue(still_current[0].enforceable)

    def test_no_total_order_over_verdicts_is_offered(self):
        """A rule set is not one rule; there is no single 'freshest' answer."""
        from norm_freshness import FreshnessReport

        self.assertFalse(hasattr(FreshnessReport, "freshness"))
        self.assertFalse(hasattr(FreshnessReport, "worst"))

    def test_an_empty_rule_set_is_ok_at_zero_coverage(self):
        report = assess([])
        self.assertTrue(report.ok)
        self.assertEqual(report.coverage, 0.0)
        self.assertEqual(report.total, 0)


class TestPurity(unittest.TestCase):
    def test_assessment_is_deterministic(self):
        args = ([pin()], {AI_ACT: state(current="2025-01-01", kind=ChangeKind.AMENDMENT)})
        first, second = assess(*args), assess(*args)
        self.assertEqual(first.verdicts, second.verdicts)
        self.assertEqual(first.determinations, second.determinations)

    def test_the_module_imports_nothing_that_reaches_the_world(self):
        import norm_freshness

        source = open(norm_freshness.__file__, encoding="utf-8").read()
        for forbidden in ("import requests", "import urllib", "import http", "import socket",
                          "datetime.now", "time.time"):
            self.assertNotIn(forbidden, source, f"{forbidden} breaks closed I/O")



class TestOptionsFollowTheCause(unittest.TestCase):
    """The options are the product. Never offer an action that cannot be taken."""

    def determination(self, kind=None, current="2025-01-01"):
        report = assess([pin()], {AI_ACT: SourceState(AI_ACT, current, kind)})
        self.assertEqual(len(report.determinations), 1)
        return report.determinations[0]

    def test_a_repeal_offers_retire_never_re_pin(self):
        """A repealed instrument is gone; there is nothing to re-pin to."""
        d = self.determination(ChangeKind.REPEAL)
        self.assertEqual(d.options, ("retire", "reassess", "halt"))
        self.assertNotIn("re-pin", d.options)

    def test_an_unresolvable_source_offers_retry_never_re_pin(self):
        """The source was never reached; re-pinning to it is not an option."""
        d = self.determination(current=None)
        self.assertEqual(d.options, ("retry", "reassess", "halt"))
        self.assertNotIn("re-pin", d.options)

    def test_an_undetermined_move_offers_investigate_not_re_pin(self):
        """Re-pinning before knowing what changed is premature."""
        d = self.determination(ChangeKind.UNKNOWN)
        self.assertEqual(d.options, ("investigate", "reassess", "halt"))

    def test_an_amendment_still_offers_re_pin(self):
        for kind in (ChangeKind.AMENDMENT, ChangeKind.COMMENCEMENT):
            with self.subTest(kind=kind):
                self.assertEqual(self.determination(kind).options, ("re-pin", "reassess", "halt"))

    def test_every_cause_offers_halt_and_reassess(self):
        for options in OPTIONS_BY_CAUSE.values():
            self.assertIn("halt", options)
            self.assertIn("reassess", options)

    def test_the_verdict_carries_the_change_kind(self):
        """A repeal and an amendment both read SUPERSEDED; the cause must survive."""
        report = assess([pin()], {AI_ACT: SourceState(AI_ACT, "2025-01-01", ChangeKind.REPEAL)})
        v = report.verdicts[0]
        self.assertIs(v.freshness, Freshness.SUPERSEDED)
        self.assertIs(v.change_kind, ChangeKind.REPEAL)


class TestFragmentObservations(unittest.TestCase):
    """A fragment-keyed observation used to be accepted and silently ignored."""

    def test_a_fragment_qualified_observation_wins(self):
        observed = {
            AI_ACT: SourceState(AI_ACT, "2025-01-01", ChangeKind.AMENDMENT),
            f"{AI_ACT}#art_14": SourceState(f"{AI_ACT}#art_14", "2024-07-12"),
        }
        report = assess([pin("r", fragment="art_14")], observed)
        self.assertIs(report.verdicts[0].freshness, Freshness.CURRENT,
                      "the more specific observation must win over the instrument-level one")

    def test_it_falls_back_to_the_bare_uri(self):
        report = assess([pin("r", fragment="art_14")],
                        {AI_ACT: SourceState(AI_ACT, "2024-07-12")})
        self.assertIs(report.verdicts[0].freshness, Freshness.CURRENT)

    def test_a_rule_without_a_fragment_is_unaffected(self):
        report = assess([RulePin("r", SourceRef(AI_ACT, "2024-07-12"))],
                        {AI_ACT: SourceState(AI_ACT, "2024-07-12")})
        self.assertIs(report.verdicts[0].freshness, Freshness.CURRENT)


if __name__ == "__main__":
    unittest.main()
