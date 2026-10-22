"""Regression tests for the cable bus review fixes (one class per review item).

Inputs are the reviewers' repro cases. Clause references are those named in the module under test; the
NEC edition-specific text is UNVERIFIED here (see the module notes).
"""

import unittest
from dataclasses import replace

from pecalc.cablebus import CableBusInput, analyse
from pecalc.cablebus_design import DesignRequest, design_options

TERM = "Most heavily loaded conductor within termination rating"
WITHSTAND = "Conductor short-circuit withstand"

LV = dict(voltage_v=480.0, current_a=2000.0, conductors_per_phase=4, size="500", material="Cu")
MV = dict(voltage_v=15000.0, current_a=2000.0, conductors_per_phase=3, size="750", insulation="EPR",
          insulation_mm=7.2, shield_mm=0.13, jacket_mm=2.0, shield_bonding="single_point", length_m=100.0)


def _check(r, prefix):
    return next((c for c in r.checks if c["name"].startswith(prefix)), None)


def _notes(r):
    return " | ".join(r.notes)


class Item1TerminationTable(unittest.TestCase):
    def test_termination_uses_table_310_16_not_free_air(self):
        r = analyse(CableBusInput(**LV, terminal_temp_c=75))
        c = _check(r, TERM)
        # Table 310.16 (raceway), 500 kcmil Cu, 75 C = 380 A (free-air Table 310.17 would give 620 A).
        self.assertEqual(c["limit"], 380.0)
        self.assertGreater(c["value"], 380.0)   # worst conductor ~531 A after sharing
        self.assertFalse(c["passed"])
        self.assertFalse(r.passed)
        self.assertIn("310.16", c["note"])


class Item2TerminationAnyMethod(unittest.TestCase):
    def test_check_present_with_datasheet_method(self):
        r = analyse(CableBusInput(**LV, terminal_temp_c=75, ampacity_method="datasheet", cable_ampacity_a=700.0))
        c = _check(r, TERM)
        self.assertIsNotNone(c)
        self.assertEqual(c["limit"], 380.0)
        self.assertFalse(c["passed"])

    def test_note_when_not_checked_above_2000_v(self):
        r = analyse(CableBusInput(**MV))
        self.assertIsNone(_check(r, TERM))
        self.assertIn("Termination temperature not checked", _notes(r))

    def test_note_when_no_table_row(self):
        # Library DLO sizes such as 444.4 kcmil have no Table 310.16 row.
        r = analyse(CableBusInput(voltage_v=600.0, current_a=500.0, conductors_per_phase=1,
                                  cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:444.4",
                                  insulation_temp_c=90))
        self.assertIsNone(_check(r, TERM))
        self.assertIn("Termination temperature not checked", _notes(r))


class Item3DefaultTerminalTemp(unittest.TestCase):
    def test_default_is_none_and_derived(self):
        self.assertIsNone(CableBusInput().terminal_temp_c)
        self.assertIsNone(DesignRequest().terminal_temp_c)

    def test_lv_defaults_to_75(self):
        r = analyse(CableBusInput(**LV))
        self.assertEqual(r.input.terminal_temp_c, 75)
        self.assertIn("110.14(C)(1)(b)", _notes(r))
        self.assertIn("370.20(A)", _notes(r))

    def test_mv_defaults_to_90(self):
        r = analyse(CableBusInput(**MV))
        self.assertEqual(r.input.terminal_temp_c, 90)
        self.assertIn("110.40", _notes(r))

    def test_explicit_value_wins(self):
        r = analyse(CableBusInput(**LV, terminal_temp_c=90))
        self.assertEqual(r.input.terminal_temp_c, 90)
        self.assertEqual(_check(r, TERM)["limit"], 430.0)   # Table 310.16, 500 kcmil Cu, 90 C
        self.assertNotIn("defaulted", _notes(r))


class Item4TierSpacing(unittest.TestCase):
    def test_tight_tier_pitch_fails(self):
        r = analyse(CableBusInput(voltage_v=600.0, current_a=2000.0, conductors_per_phase=6, tiers=2, size="500",
                                  tier_spacing_mm=40.0))
        c = _check(r, "Tier spacing")
        self.assertIsNotNone(c)
        self.assertFalse(c["passed"])
        self.assertFalse(r.passed)

    def test_default_tier_pitch_passes(self):
        r = analyse(CableBusInput(voltage_v=600.0, current_a=2000.0, conductors_per_phase=6, tiers=2, size="500"))
        self.assertTrue(_check(r, "Tier spacing")["passed"])

    def test_single_tier_has_no_tier_check(self):
        r = analyse(CableBusInput(voltage_v=600.0, current_a=1000.0, conductors_per_phase=3, size="500"))
        self.assertIsNone(_check(r, "Tier spacing"))


class Item5FaultWithoutClearingTime(unittest.TestCase):
    def test_visible_failure(self):
        r = analyse(CableBusInput(voltage_v=600.0, current_a=1000.0, conductors_per_phase=3, size="500",
                                  fault_ka=50.0))
        c = _check(r, WITHSTAND)
        self.assertIsNotNone(c)
        self.assertFalse(c["passed"])
        self.assertIn("fault_clearing_s", c["name"] + c["note"])
        self.assertFalse(r.passed)

    def test_with_clearing_time_it_is_a_real_check(self):
        r = analyse(CableBusInput(voltage_v=600.0, current_a=1000.0, conductors_per_phase=3, size="500",
                                  fault_ka=10.0, fault_clearing_s=0.1))
        c = _check(r, WITHSTAND)
        self.assertTrue(c["passed"])
        self.assertGreater(c["value"], 10.0)

    def test_designer_applies_the_check(self):
        base = dict(voltage_v=600.0, current_a=1000.0, fault_ka=100.0, sizes=("500",))
        short = design_options(DesignRequest(**base, fault_clearing_s=0.05))
        long_ = design_options(DesignRequest(**base, fault_clearing_s=5.0))
        self.assertTrue(any(o.passed for o in short.options))
        self.assertFalse(any(o.passed for o in long_.options))
        self.assertTrue(all(any(WITHSTAND in f for f in o.failed_checks) for o in long_.options))
        self.assertEqual(short.options[0].case_inputs["fault_clearing_s"], 0.05)


class Item6ShieldVoltageLimit(unittest.TestCase):
    def test_note_when_single_point_and_no_limit(self):
        r = analyse(CableBusInput(**MV))
        self.assertIn("standing voltage was not checked against a limit", _notes(r))

    def test_no_note_when_limit_given(self):
        r = analyse(CableBusInput(**MV, shield_voltage_limit_v=1000.0))
        self.assertNotIn("not checked against a limit", _notes(r))

    def test_designer_passes_limit_through(self):
        req = DesignRequest(voltage_v=15000.0, current_a=2000.0, insulation="EPR", insulation_mm=7.2,
                            shield_mm=0.13, jacket_mm=2.0, shield_voltage_limit_v=0.01)
        r = design_options(req)
        self.assertEqual(r.options[0].case_inputs["shield_voltage_limit_v"], 0.01)
        self.assertTrue(all(any("Shield standing voltage" in f for f in o.failed_checks) for o in r.options))


class Item7InputValidation(unittest.TestCase):
    def _raises(self, text, **kw):
        with self.assertRaisesRegex(ValueError, text):
            analyse(CableBusInput(**{**LV, **kw}))

    def test_current(self):
        self._raises("current_a must be greater than 0 A", current_a=0.0)
        self._raises("current_a must be greater than 0 A", current_a=-100.0)

    def test_length_and_frequency(self):
        self._raises("length_m must be greater than 0 m", length_m=0.0)
        self._raises("frequency_hz must be greater than 0 Hz", frequency_hz=-60.0)

    def test_counts(self):
        self._raises("tiers must be a whole number of at least 1", tiers=0)
        self._raises("conductors_per_phase must be a whole number of at least 1", conductors_per_phase=0)

    def test_fault_ka(self):
        self._raises("fault_ka must be 0 or greater", fault_ka=-5.0)

    def test_od_must_exceed_bare_conductor(self):
        # 500 kcmil bare diameter is about 23 mm
        self._raises("cable_od_mm .* must be greater than the conductor bare diameter", cable_od_mm=10.0)

    def test_designer(self):
        for kw, text in ((dict(current_a=0.0), "current_a must be greater than 0 A"),
                         (dict(length_m=-1.0), "length_m must be greater than 0 m"),
                         (dict(frequency_hz=0.0), "frequency_hz must be greater than 0 Hz"),
                         (dict(tier_options=(0,)), "tiers"),
                         (dict(fault_ka=-1.0), "fault_ka must be 0 or greater")):
            with self.subTest(kw=kw), self.assertRaisesRegex(ValueError, text):
                design_options(DesignRequest(**kw))


class Item8AmbientAtConductorRating(unittest.TestCase):
    MSG = r"ambient_c \(90 C\) must be below the conductor temperature rating \(90 C\)"

    def test_table_method(self):
        with self.assertRaisesRegex(ValueError, self.MSG):
            analyse(CableBusInput(**LV, ambient_c=90.0))

    def test_datasheet_method(self):
        with self.assertRaisesRegex(ValueError, self.MSG):
            analyse(CableBusInput(**LV, ambient_c=90.0, ampacity_method="datasheet", cable_ampacity_a=600.0))

    def test_designer(self):
        with self.assertRaisesRegex(ValueError, self.MSG):
            design_options(DesignRequest(voltage_v=480.0, current_a=2000.0, ambient_c=90.0))

    def test_calculated_method(self):
        with self.assertRaisesRegex(ValueError, self.MSG):
            analyse(CableBusInput(**MV, ambient_c=90.0))


class Item9DesignerRanking(unittest.TestCase):
    def test_tags_and_rank_one_are_passing(self):
        r = design_options(DesignRequest(voltage_v=480.0, current_a=2000.0, fault_ka=100.0, x_over_r=20.0,
                                         fault_clearing_s=0.5))
        self.assertTrue(r.options)
        for o in r.options:
            if o.tags:
                self.assertTrue(o.passed, f"tagged option failing: {o.label} {o.failed_checks}")
        self.assertTrue(r.options[0].passed)
        seen_fail = False
        for o in r.options:      # passing options come before failing ones
            seen_fail = seen_fail or not o.passed
            if seen_fail:
                self.assertFalse(o.passed)

    def test_block_check_failure_is_untagged(self):
        r = design_options(DesignRequest(voltage_v=480.0, current_a=2000.0, fault_ka=100.0, x_over_r=20.0,
                                         block_rated_load_n=500.0))
        self.assertTrue(all(not o.tags for o in r.options if not o.passed))


class Item10Mv600VWallNote(unittest.TestCase):
    def test_note_for_1000_v_without_od(self):
        r = analyse(CableBusInput(voltage_v=1000.0, current_a=1000.0, conductors_per_phase=2, size="750"))
        self.assertIn("estimated from a 600 V insulation wall", _notes(r))
        self.assertIn("cable_od_mm", _notes(r))

    def test_no_note_with_od_or_at_600_v(self):
        r = analyse(CableBusInput(voltage_v=1000.0, current_a=1000.0, conductors_per_phase=2, size="750",
                                  cable_od_mm=40.0))
        self.assertNotIn("600 V insulation wall", _notes(r))
        r = analyse(CableBusInput(voltage_v=600.0, current_a=1000.0, conductors_per_phase=2, size="750"))
        self.assertNotIn("600 V insulation wall", _notes(r))

    def test_designer_note(self):
        r = design_options(DesignRequest(voltage_v=1000.0, current_a=1000.0, sizes=("750",)))
        self.assertIn("600 V insulation wall", " ".join(r.notes))


class Item11EngineeringSupervisionClause(unittest.TestCase):
    def test_calculated_method_cites_310_14b_and_315_60b(self):
        r = analyse(CableBusInput(**MV))
        text = _notes(r)
        self.assertIn("310.14(B)", text)
        self.assertIn("315.60(B)", text)


if __name__ == "__main__":
    unittest.main()
