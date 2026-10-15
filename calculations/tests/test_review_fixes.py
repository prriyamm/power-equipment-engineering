"""Regression tests for the independent review of the engine (JS port review).

Each expected value is derived by hand in the comment next to it. Code-table
values used in the derivations are the repository's UNVERIFIED data (NEC
Tables 310.16 / 310.17 / 240.4(D) / Ch. 9 Table 9 entered from memory or from
secondary reprints), not values checked against the printed code.
"""

import json
import math
import unittest

from pecalc import ampacity as amp
from pecalc import conductors as cond
from pecalc import reactance_derived as rxd
from pecalc.sizing import FeederInput, evaluate, size_feeder, small_conductor_limit_a


class SmallConductorLimit(unittest.TestCase):
    """Fix 1: NEC 240.4(D)."""

    def test_data_is_unverified_with_expected_limits(self):
        data = json.loads((amp.DATA / "nec_240_4d_small_conductors.json").read_text())
        self.assertEqual(data["_meta"]["status"], "UNVERIFIED")
        self.assertIn("memory", data["_meta"]["note"])
        self.assertEqual(data["Cu"], {"18": 7, "16": 10, "14": 15, "12": 20, "10": 30})
        self.assertEqual(data["Al"], {"12": 15, "10": 25})
        self.assertIsNone(small_conductor_limit_a("Al", "8"))
        self.assertIsNone(small_conductor_limit_a("Cu", "8"))

    def test_20a_at_75c_terminal_needs_12_cu_not_14(self):
        # 20 A non-continuous, 75 C terminal: Table 310.16 14 AWG Cu 75 C column = 20 A >= 20 A, so the
        # terminal check alone accepts 14 AWG (the old answer). 240.4(D): 14 Cu max OCPD 15 A < 20 A
        # minimum device -> fails. 12 Cu: 75 C 25 A >= 20, OCPD limit 20 A >= 20 -> 12 AWG.
        r = size_feeder(FeederInput(noncontinuous_a=20, terminal_temp_c=75, length_m=5))
        self.assertEqual((r.recommended.sets, r.recommended.size), (1, "12"))
        fourteen = evaluate(r.input, "14", 1)
        d = {c.clause: c for c in fourteen.checks}["NEC 240.4(D) [data UNVERIFIED]"]
        self.assertFalse(d.passed)
        self.assertEqual((d.value, d.limit), (20.0, 15.0))

    def test_16a_continuous_needs_12_cu(self):
        # 16 A continuous: minimum device 1.25 x 16 = 20 A. 14 Cu (75 C 20 A) passes 110.14(C) but its
        # 240.4(D) limit is 15 A < 20 A; 12 Cu limit 20 A -> 12 AWG.
        r = size_feeder(FeederInput(continuous_a=16, terminal_temp_c=75, length_m=5))
        self.assertEqual(r.recommended.size, "12")

    def test_20a_aluminum_needs_10_al(self):
        # 20 A non-continuous Al, 75 C terminal: 12 Al 75 C column 20 A passes, but 240.4(D) 12 Al = 15 A
        # < 20 A. 10 Al: 75 C 30 A, 240.4(D) 25 A >= 20 A -> 10 AWG Al.
        r = size_feeder(FeederInput(noncontinuous_a=20, terminal_temp_c=75, length_m=5, material="Al"))
        self.assertEqual(r.recommended.size, "10")


class FreeAirTerminations(unittest.TestCase):
    """Fix 2: NEC 110.14(C) uses Table 310.16 even for conductors in free air."""

    def test_400a_continuous_free_air(self):
        # Terminal requirement 1.25 x 400 = 500 A at the 75 C column of Table 310.16:
        #   2 sets: 250 A/set -> 2/0 (175 A) fails (2 x 175 = 350 A, 30 % short); 250 kcmil (255 A) passes.
        #   3 sets: 166.7 A/set -> 2/0 (175 A) passes; total 3 x 67.4 = 202 mm2, the least area.
        # Old code used Table 310.17 (2/0 Cu 75 C free air = 265 A) and returned 2 x 2/0.
        r = size_feeder(FeederInput(continuous_a=400, installation="free_air", length_m=5))
        self.assertEqual((r.recommended.sets, r.recommended.size), (3, "2/0"))
        by_sets = {o.sets: o.size for o in [r.recommended] + r.alternatives}
        self.assertEqual(by_sets[2], "250")
        two_by_2_0 = evaluate(r.input, "2/0", 2)
        term = two_by_2_0.checks[1]
        self.assertIn("Table 310.16", term.note)
        self.assertEqual((term.value, term.limit, term.passed), (175.0, 250.0, False))

    def test_conductor_ampacity_still_from_310_17(self):
        # 3 x 2/0 Cu in free air, 90 C insulation, 30 C ambient: derated = Table 310.17 90 C 2/0 = 300 A
        # (> 175 A at the terminal), so allowable = min(300, 175) = 175 A per set.
        r = size_feeder(FeederInput(continuous_a=400, installation="free_air", length_m=5))
        derated = [c for c in r.recommended.checks if c.name == "Derated ampacity >= load"][0]
        self.assertEqual(derated.value, amp.table_ampacity("NEC", "free_air", "Cu", "2/0", 90))
        self.assertEqual(r.recommended.ampacity_per_set_a, 175.0)


class DoeTestPoint(unittest.TestCase):
    """Fix 3: DOE class and test load from the primary voltage."""

    def _r(self, **kw):
        from pecalc.transformer import TransformerInput, design
        return design(TransformerInput(**kw))

    def _check(self, r, load, temp):
        # eff = S L / (S L + NLL + LL_T L^2), LL corrected from the reference temperature to `temp`:
        # LL_T = LL (234.5 + T) / (234.5 + Tref)  (Cu windings).
        s = r.input.kva * 1000
        nll, ll, tref = r.losses["no_load_w"], r.losses["load_loss_w"], r.losses["reference_temp_c"]
        ll_t = ll * (234.5 + temp) / (234.5 + tref)
        expect = s * load / (s * load + nll + ll_t * load ** 2) * 100
        self.assertEqual(r.performance["doe_point"]["load"], load)
        self.assertAlmostEqual(r.performance["doe_point"]["efficiency_pct"], expect, delta=0.002)

    def test_liquid_immersed_50pct(self):
        self._check(self._r(kind="liquid", hv_v=13800, lv_v=480, kva=1500), 0.50, 55.0)

    def test_medium_voltage_dry_type_50pct(self):
        # 13.8 kV primary > 600 V -> medium-voltage dry-type, 50 % (old code: 35 % from the 480 V LV side).
        self._check(self._r(kind="dry", hv_v=13800, lv_v=480, kva=1500), 0.50, 75.0)

    def test_low_voltage_dry_type_35pct(self):
        # 480 V primary <= 600 V -> low-voltage dry-type, 35 %.
        self._check(self._r(kind="dry", hv_v=480, lv_v=208, kva=75), 0.35, 75.0)

    def test_class_function(self):
        from pecalc.transformer import doe_test_point
        self.assertEqual(doe_test_point("dry", 600), ("low-voltage dry-type", 0.35))
        self.assertEqual(doe_test_point("dry", 601), ("medium-voltage dry-type", 0.50))
        self.assertEqual(doe_test_point("liquid", 480), ("liquid-immersed", 0.50))


class PhasorSourceImpedance(unittest.TestCase):
    """Fix 4: source + transformer impedance as phasors."""

    def test_source_impedance_phasor(self):
        from pecalc.transformer import source_impedance_pu
        # 1500 kVA on a 50 MVA source: |Zs| = 1.5 / 50 = 0.03 pu; X/R = 1 -> 0.03 / sqrt(2) (1 + j).
        z = source_impedance_pu(1500, 50, 1.0)
        self.assertAlmostEqual(z.real, 0.03 / math.sqrt(2), places=12)
        self.assertAlmostEqual(z.imag, 0.03 / math.sqrt(2), places=12)
        self.assertEqual(source_impedance_pu(1500, None, 10.0), 0j)

    def test_fault_current_uses_phasor_sum(self):
        from pecalc.transformer import TransformerInput, design
        r = design(TransformerInput(kva=1500, hv_v=13800, lv_v=480, source_mva=50, source_x_over_r=1.0))
        rp, xp = r.impedance["r_pct"] / 100, r.impedance["x_pct"] / 100     # 0.0091, 0.0488 pu
        zs = 0.03 / math.sqrt(2)                                            # 0.02121 pu each part
        i_fl = 1.5e6 / (math.sqrt(3) * 480)                                 # 1804.2 A
        # Phasor: |(0.0091 + 0.0212) + j(0.0488 + 0.0212)| = |0.0303 + j0.0700| = 0.0763 pu -> 23.65 kA.
        phasor = i_fl / abs(complex(rp + zs, xp + zs)) / 1000
        # Old magnitude sum: 0.0497 + 0.0300 = 0.0797 pu -> 22.64 kA (4 % low).
        magnitude = i_fl / (math.hypot(rp, xp) + 0.03) / 1000
        self.assertAlmostEqual(r.short_circuit["lv_fault_ka_rms"], phasor, delta=0.03)
        self.assertGreater(r.short_circuit["lv_fault_ka_rms"] - magnitude, 0.8)
        # Combined X/R = 0.0700 / 0.0303 = 2.31, used for the peak factor.
        self.assertAlmostEqual(r.short_circuit["total_x_over_r"], (xp + zs) / (rp + zs), delta=0.02)

    def test_infinite_bus_unchanged(self):
        from pecalc.transformer import TransformerInput, design
        r = design(TransformerInput(kva=1500, hv_v=13800, lv_v=480))
        i_fl = 1.5e6 / (math.sqrt(3) * 480)
        self.assertAlmostEqual(r.short_circuit["lv_fault_ka_rms"], i_fl / (r.impedance["z_pct"] / 100) / 1000,
                               delta=0.05)


class DerivedTable9(unittest.TestCase):
    """Fix 5: derived reactance rows; must match power-studio-web reactanceDerived.js."""

    def test_status_and_table9_unchanged(self):
        self.assertEqual(rxd.DERIVED_STATUS,
                         "DERIVED — UNVERIFIED (interpolated/extrapolated from NEC Table 9, not a published value)")
        for rw in rxd.RACEWAYS:
            for s in rxd.DERIVED_SIZES:
                self.assertNotIn(s, rxd.table9()[rw])

    def test_values_match_web_port(self):
        # PVC: 900 = 0.038 + ln(900/750)/ln(1000/750) x (0.037 - 0.038) = 0.038 - 0.6338 x 0.001 = 0.0374
        #      2000 = 0.038 - ln(2000/750)/ln(4/3) x 0.001 = 0.038 - 3.4094 x 0.001 = 0.0346
        # Steel: 900 = 0.048 - 0.6338 x 0.002 = 0.0467; 2000 = 0.048 - 3.4094 x 0.002 = 0.0412
        # 700 (PVC): 0.039 + ln(700/600)/ln(750/600) x (0.038 - 0.039) = 0.039 - 0.6908 x 0.001 = 0.0383
        expect = {("pvc", "900"): 0.0374, ("pvc", "2000"): 0.0346, ("steel", "900"): 0.0467,
                  ("steel", "2000"): 0.0412, ("pvc", "700"): 0.0383, ("aluminum", "900"): 0.0374}
        for (rw, s), x in expect.items():
            with self.subTest(raceway=rw, size=s):
                self.assertEqual(rxd.reactance_per_1000ft(s, rw), (x, True))
        self.assertEqual(rxd.reactance_per_1000ft("750", "pvc"), (0.038, False))

    def test_floor_is_touching_trefoil(self):
        # Floor at 2000 kcmil: GMD = OD = 1.632 + 2 x 0.095 = 1.822 in, GMR = 0.7788 x 1.632/2 = 0.6355 in;
        # X = 2 pi 60 x 2e-7 ln(1.822 / 0.6355) x 304.8 = 0.0242 ohm/1000 ft, below 0.0346, so not binding.
        self.assertAlmostEqual(rxd.floor_per_1000ft("2000"), 0.0242, delta=0.00005)
        for rw in rxd.RACEWAYS:
            for s in rxd.DERIVED_SIZES:
                self.assertGreaterEqual(rxd.derived_table()[rw][s], round(rxd.floor_per_1000ft(s), 4))

    def test_feeder_uses_derived_and_warns(self):
        # 900 kcmil in steel conduit: X = 0.0467 ohm/1000 ft = 0.0467 / 0.3048 = 0.1532 ohm/km
        # (old fallback: touching trefoil 0.0248 ohm/1000 ft = 0.0814 ohm/km, 47 % low).
        inp = FeederInput(continuous_a=400, length_m=100, conduit="steel", terminal_temp_c=75, sets=1)
        o = evaluate(inp, "900", 1)
        self.assertAlmostEqual(o.x_ohm_per_km, 0.0467 / 0.3048, places=3)
        self.assertIn("DERIVED", o.checks[-1].note)
        r = size_feeder(FeederInput(continuous_a=330, length_m=10, conduit="pvc", sets=1, terminal_temp_c=75))
        # 1.25 x 330 = 412.5 A: 600 kcmil (420 A) - in Table 9, so no warning.
        self.assertEqual(r.recommended.size, "600")
        self.assertFalse(any("DERIVED" in n for n in r.notes))
        r = size_feeder(FeederInput(continuous_a=360, length_m=10, conduit="pvc", sets=1, terminal_temp_c=75))
        # 1.25 x 360 = 450 A: 600 kcmil (420 A) fails, 700 kcmil (460 A) passes -> derived reactance warning.
        self.assertEqual(r.recommended.size, "700")
        self.assertTrue(any("DERIVED" in n for n in r.notes))


class InvalidInputs(unittest.TestCase):
    """Fix 6: one ValueError per bad input, everywhere it is accepted."""

    def test_feeder(self):
        for bad in ({"voltage_v": 0}, {"voltage_v": -480}, {"power_factor": 0}, {"power_factor": 1.2},
                    {"power_factor": -0.9}, {"fault_ka": 30, "fault_clearing_s": -0.1},
                    {"fault_ka": 30, "fault_clearing_s": 0}):
            with self.subTest(**bad), self.assertRaises(ValueError):
                size_feeder(FeederInput(continuous_a=100, **bad))

    def test_transformer(self):
        from pecalc.transformer import TransformerInput, design
        for bad in ({"hv_v": 0}, {"lv_v": -480}, {"power_factor": 0}, {"power_factor": 1.5},
                    {"fault_duration_s": -1}, {"source_x_over_r": 0}, {"source_mva": 50, "source_x_over_r": -3}):
            with self.subTest(**bad), self.assertRaises(ValueError):
                design(TransformerInput(**bad))

    def test_bus_forces_sharing_thermal(self):
        from pecalc.forces import peak_factor
        from pecalc.impedance import balanced_three_phase
        from pecalc.switchgear import BusInput, analyse_bus
        from pecalc.thermal import CableConstruction, free_air_ampacity
        cases = [
            lambda: analyse_bus(BusInput(voltage_v=0)),
            lambda: analyse_bus(BusInput(fault_ka=50, x_over_r=0)),
            lambda: peak_factor(-1),
            lambda: balanced_three_phase(100, 0),
            lambda: balanced_three_phase(100, 1.01),
            lambda: free_air_ampacity(CableConstruction("500", voltage_v=0)),
        ]
        for i, f in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(ValueError):
                f()

    def test_cablebus(self):
        from pecalc.cablebus import CableBusInput, analyse
        for v in (0, -600, float("nan")):
            with self.subTest(voltage_v=v), self.assertRaisesRegex(ValueError, "voltage_v must be"):
                analyse(CableBusInput(voltage_v=v))

    def test_message_names_the_input(self):
        with self.assertRaisesRegex(ValueError, r"power_factor must be in the range \(0, 1\]"):
            size_feeder(FeederInput(continuous_a=100, power_factor=1.2))
        with self.assertRaisesRegex(ValueError, "voltage_v must be greater than 0 V"):
            size_feeder(FeederInput(continuous_a=100, voltage_v=0))


class Table31016Aluminum8(unittest.TestCase):
    """Fix 7: NEC Table 310.16 8 AWG Al (UNVERIFIED; public reprints of the table)."""

    def test_8_awg_al_row(self):
        # Reprints of Table 310.16: 8 AWG Al 60 / 75 / 90 C = 30 / 40 / 45 A (data previously had 35 A at 60 C).
        self.assertEqual([amp.table_ampacity("NEC", "raceway", "Al", "8", t) for t in (60, 75, 90)],
                         [30.0, 40.0, 45.0])
        self.assertEqual(amp.table_info("NEC", "raceway").status, "UNVERIFIED")

    def test_feeder_at_33a_al_60c(self):
        # 33 A non-continuous Al, 60 C terminal: 8 AWG Al 60 C = 30 A < 33 A -> 6 AWG Al (60 C 40 A).
        # Before the correction 8 AWG (35 A) was accepted.
        r = size_feeder(FeederInput(noncontinuous_a=33, material="Al", terminal_temp_c=60, length_m=5))
        self.assertEqual(r.recommended.size, "6")


class EprThermalResistivity(unittest.TestCase):
    """Fix 8: IEC 60287-2-1 Table 1 EPR 3.5 K m/W up to 3 kV, 5.0 above (UNVERIFIED, secondary sources)."""

    def test_resistivity_by_rated_voltage(self):
        from pecalc.thermal import insulation_resistivity
        self.assertEqual(insulation_resistivity("EPR", 600), 3.5)
        self.assertEqual(insulation_resistivity("EPR", 3000), 3.5)
        self.assertEqual(insulation_resistivity("EPR", 15000), 5.0)
        self.assertEqual(insulation_resistivity("XLPE", 15000), 3.5)

    def test_t1_at_0_6_and_15_kv(self):
        from pecalc.thermal import CableConstruction, free_air_ampacity
        # 500 kcmil: dc = 0.813 in = 20.650 mm; 1.65 mm wall: ln(1 + 3.30 / 20.650) = 0.14825.
        #   0.6 kV: T1 = 3.5 / (2 pi) x 0.14825 = 0.08258 K m/W (was 5.0 / (2 pi) x 0.14825 = 0.11797).
        # 15 kV, 4.45 mm wall: ln(1 + 8.90 / 20.650) = 0.35838; T1 = 5.0 / (2 pi) x 0.35838 = 0.28518 (unchanged).
        lv = free_air_ampacity(CableConstruction("500", insulation="EPR", insulation_mm=1.65, voltage_v=600),
                               40, "trefoil_touching")
        mv = free_air_ampacity(CableConstruction("500", insulation="EPR", insulation_mm=4.45, voltage_v=15000,
                                                 jacket_mm=2.0), 40, "trefoil_touching")
        self.assertAlmostEqual(lv.t1, 0.08258, places=5)
        self.assertAlmostEqual(mv.t1, 0.28518, places=5)
        # LV ampacity rises (577 -> 585 A for this case); explicit 15 kV rating restores the old value.
        old = free_air_ampacity(CableConstruction("500", insulation="EPR", insulation_mm=1.65, voltage_v=600,
                                                  rated_voltage_v=15000), 40, "trefoil_touching")
        self.assertGreater(lv.ampacity_a, old.ampacity_a)
        self.assertAlmostEqual(old.t1, 0.11797, places=5)


class CableBusShortCircuitWithstand(unittest.TestCase):
    """P17: ICEA P-32-382 adiabatic conductor withstand in the cable bus module (same formula as sizing.py)."""

    @staticmethod
    def _sc(r):
        return [c for c in r.checks if c["name"] == "Conductor short-circuit withstand"]

    def test_three_750_cu_per_phase_half_second(self):
        from pecalc.cablebus import CableBusInput, analyse
        # A = 3 x 750 000 = 2 250 000 cmil; Cu: K = 0.0297, T0 = 234; T1 = 90 C, T2 = 250 C, t = 0.5 s.
        # (250 + 234) / (90 + 234) = 484 / 324 = 1.493827; log10 = 0.174300
        # 0.0297 x 0.174300 / 0.5 = 0.0103534; sqrt = 0.101752
        # I = 2 250 000 x 0.101752 = 228 942 A = 228.94 kA >= 50 kA -> pass
        r = analyse(CableBusInput(fault_ka=50, fault_clearing_s=0.5))
        (c,) = self._sc(r)
        self.assertEqual(c["clause"], "ICEA P-32-382")
        self.assertAlmostEqual(c["value"], 228.94, places=2)
        self.assertEqual(c["limit"], 50)
        self.assertTrue(c["passed"])

    def test_single_4_0_cu_one_second_fails(self):
        from pecalc.cablebus import CableBusInput, analyse
        # A = 211 600 cmil; 0.0297 x 0.174300 / 1.0 = 0.0051767; sqrt = 0.071949
        # I = 211 600 x 0.071949 = 15 224 A = 15.22 kA < 20 kA -> fail
        r = analyse(CableBusInput(size="4/0", conductors_per_phase=1, current_a=300, fault_ka=20,
                                  fault_clearing_s=1.0))
        (c,) = self._sc(r)
        self.assertAlmostEqual(c["value"], 15.22, places=2)
        self.assertFalse(c["passed"])
        self.assertFalse(r.passed)

    def test_matches_feeder_formula(self):
        # Same helper as sizing._short_circuit_check: 3 sets of 750 Cu at 0.5 s gives the same 228.9 kA.
        f = evaluate(FeederInput(continuous_a=1500, voltage_v=600, terminal_temp_c=75, fault_ka=50,
                                  fault_clearing_s=0.5), "750", 3)
        sc = [c for c in f.checks if c.clause == "ICEA P-32-382"][0]
        self.assertEqual(sc.value, 228.9)
        self.assertAlmostEqual(cond.adiabatic_withstand_a("Cu", 2_250_000, 90, 250, 0.5), 228941.68, places=1)

    def test_skipped_without_clearing_time(self):
        from pecalc.cablebus import CableBusInput, analyse
        r = analyse(CableBusInput(fault_ka=50))
        self.assertEqual(self._sc(r), [])
        self.assertIn("Conductor short-circuit withstand not checked: give fault_clearing_s.", r.notes)
        self.assertEqual(self._sc(analyse(CableBusInput(fault_clearing_s=0.5))), [])

    def test_invalid_clearing_time(self):
        from pecalc.cablebus import CableBusInput, analyse
        for t in (0, -0.1, float("nan")):
            with self.subTest(t=t), self.assertRaisesRegex(ValueError, "fault_clearing_s must be"):
                analyse(CableBusInput(fault_ka=50, fault_clearing_s=t))


if __name__ == "__main__":
    unittest.main()
