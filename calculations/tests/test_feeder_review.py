"""Regression tests for the feeder sizing review (terminal column, 110.14(C)(1) default, scope, validation).

Ampacities are the repository's UNVERIFIED NEC Table 310.16 values.
"""

import math
import unittest

from pecalc import ampacity as amp
from pecalc.lugs import LugInput, select_lugs
from pecalc.sizing import FeederInput, evaluate, size_feeder

TERM = "Terminal-column ampacity >= 125 % continuous + non-continuous"


def _check(opt, name):
    return next(c for c in opt.checks if c.name == name)


class TerminalColumn(unittest.TestCase):
    def test_terminal_above_insulation_uses_insulation_column(self):
        # 400 A continuous x 1.25 = 500 A over 3 sets = 166.7 A per set. 3 x 1/0 Cu: 75 C column 150 A < 166.7,
        # although the 90 C terminal column (170 A) alone would pass. The conductor cannot use the 90 C column.
        inp = FeederInput(continuous_a=400, insulation_temp_c=75, terminal_temp_c=90, sets=3, length_m=5)
        opt = evaluate(inp, "1/0", 3)
        c = _check(opt, TERM)
        self.assertEqual(c.value, amp.table_ampacity("NEC", "raceway", "Cu", "1/0", 75))
        self.assertFalse(c.passed)
        self.assertIn("110.14(C)", c.note)
        r = size_feeder(inp)
        self.assertNotEqual(r.recommended.size, "1/0")

    def test_60c_insulation_with_75c_terminal(self):
        # 200 A continuous x 1.25 = 250 A, one set. 250 kcmil Cu 60 C = 215 A < 250 A (75 C column 255 A is not usable).
        inp = FeederInput(continuous_a=200, insulation_temp_c=60, terminal_temp_c=75, sets=1, length_m=5)
        opt = evaluate(inp, "250", 1)
        self.assertFalse(_check(opt, TERM).passed)
        self.assertEqual(_check(opt, TERM).value, amp.table_ampacity("NEC", "raceway", "Cu", "250", 60))
        self.assertNotEqual(size_feeder(inp).recommended.size, "250")


class DefaultTerminalTemp(unittest.TestCase):
    def test_default_is_per_candidate_size(self):
        # 105 A non-continuous: 2 AWG Cu at the 60 C default column is 95 A (< 105 A); 1 AWG is 110 A.
        r = size_feeder(FeederInput(noncontinuous_a=105, length_m=1))
        self.assertEqual(r.recommended.size, "1")
        self.assertEqual(r.recommended.sets, 1)
        self.assertTrue(any("60 C" in n and "110.14(C)(1)" in n for n in r.recommended.notes))

    def test_default_75c_for_large_size_and_explicit_kept(self):
        r = size_feeder(FeederInput(noncontinuous_a=150, length_m=1))
        self.assertTrue(any("75 C" in n and "default" in n for n in r.recommended.notes))
        r = size_feeder(FeederInput(noncontinuous_a=150, length_m=1, terminal_temp_c=75))
        self.assertTrue(any("as given" in n for n in r.recommended.notes))

    def test_lugs_get_no_derived_marking(self):
        inp = FeederInput(noncontinuous_a=105, length_m=1)
        r = size_feeder(inp)
        self.assertIsNone(inp.terminal_temp_c)
        self.assertIsNone(r.lugs.input.equipment_terminal_temp_c)
        self.assertIn("defaults", r.lugs.terminal_temp_basis)


class VoltageScope(unittest.TestCase):
    def test_nec_above_1000_v_rejected(self):
        with self.assertRaises(ValueError) as cm:
            size_feeder(FeederInput(voltage_v=1500, continuous_a=100))
        self.assertIn("1000 V", str(cm.exception))
        self.assertIn("Article 235", str(cm.exception))

    def test_nec_1000_v_ok_and_cec_keeps_2000_v(self):
        self.assertIsNotNone(size_feeder(FeederInput(voltage_v=1000, continuous_a=100)).recommended)
        with self.assertRaises(ValueError) as cm:
            size_feeder(FeederInput(code="CEC", voltage_v=2500, continuous_a=100))
        self.assertIn("2000 V", str(cm.exception))


class Validation(unittest.TestCase):
    def _bad(self, name, **kw):
        base = dict(continuous_a=100)
        base.update(kw)
        with self.assertRaises(ValueError) as cm:
            size_feeder(FeederInput(**base))
        self.assertIn(name, str(cm.exception))

    def test_load_currents(self):
        self._bad("continuous_a", continuous_a=-10, noncontinuous_a=50)
        self._bad("noncontinuous_a", noncontinuous_a=-10)
        self._bad("load current", continuous_a=0)

    def test_scalars(self):
        self._bad("length_m", length_m=0)
        self._bad("length_m", length_m=-5)
        self._bad("sets", sets=0)
        self._bad("sets", sets=-1)
        self._bad("sets", sets=1.5)
        self._bad("phases", phases=2)
        self._bad("frequency_hz", frequency_hz=0)
        self._bad("current_carrying_per_raceway", current_carrying_per_raceway=0)
        self._bad("ambient_c", ambient_c=150)
        self._bad("ambient_c", ambient_c=-60)
        self._bad("conductor_temp_for_vd_c", conductor_temp_for_vd_c=300)

    def test_nan_inf(self):
        for name in ("continuous_a", "noncontinuous_a", "length_m", "frequency_hz", "ambient_c",
                     "conductor_temp_for_vd_c", "voltage_v", "max_vd_pct", "power_factor"):
            for bad in (math.nan, math.inf):
                self._bad(name, **{name: bad})


class ShortCircuit(unittest.TestCase):
    def _raises(self, **kw):
        with self.assertRaises(ValueError) as cm:
            size_feeder(FeederInput(continuous_a=100, **kw))
        self.assertIn("fault_ka", str(cm.exception))

    def test_exactly_one_fault_input_rejected(self):
        self._raises(fault_ka=20)
        self._raises(fault_clearing_s=0.5)

    def test_thermoset_limit_note(self):
        r = size_feeder(FeederInput(continuous_a=100, fault_ka=10, fault_clearing_s=0.5))
        c = next(c for c in r.recommended.checks if c.name.startswith("Short-circuit"))
        self.assertIn("thermoset", c.note)
        self.assertIn("UNVERIFIED", c.note)
        self.assertIn("ICEA P-32-382", c.note)


class RacewayGrouping(unittest.TestCase):
    def test_grouping_assumption_notes(self):
        r = size_feeder(FeederInput(continuous_a=400, length_m=5, sets=3))
        self.assertTrue(any("current_carrying_per_raceway" in n and "own raceway" in n for n in r.notes))
        self.assertTrue(any("separate raceways per set" in n for n in r.recommended.notes))

    def test_no_per_option_note_when_within_limit(self):
        r = size_feeder(FeederInput(continuous_a=100, length_m=5, sets=1))
        self.assertFalse(any("separate raceways" in n for n in r.recommended.notes))

    def test_ocpd_note_on_every_result(self):
        for code in ("NEC", "CEC"):
            r = size_feeder(FeederInput(code=code, continuous_a=100, length_m=5, allow_placeholder_data=True))
            self.assertTrue(any("not checked here" in n for n in r.notes), code)


class LugValidation(unittest.TestCase):
    def _bad(self, name, **kw):
        with self.assertRaises(ValueError) as cm:
            select_lugs(LugInput(**kw))
        self.assertIn(name, str(cm.exception))

    def test_bad_inputs(self):
        self._bad("sets_per_phase", sets_per_phase=0)
        self._bad("phases", phases=2)
        self._bad("circuit_current_a", circuit_current_a=0)
        self._bad("circuit_current_a", circuit_current_a=math.nan)
        self._bad("equipment_terminal_temp_c", equipment_terminal_temp_c=0)
        self._bad("equipment_terminal_temp_c", equipment_terminal_temp_c=80)
        self._bad("code", code="IEC")
        self._bad("material", material="Fe")

    def test_none_means_unset(self):
        r = select_lugs(LugInput(equipment_terminal_temp_c=None))
        self.assertIn("defaults", r.terminal_temp_basis)
        r = select_lugs(LugInput(equipment_terminal_temp_c=90))
        self.assertEqual(r.terminal_temp_c, 90)


if __name__ == "__main__":
    unittest.main()
