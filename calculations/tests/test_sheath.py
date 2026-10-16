"""Shield (sheath) standing voltage with single-point bonding, and the bonding comparison.

Hand checks use the impedance module's own mutual impedance (impedance_matrix):
    z_ij = pi^2 f 1e-7 + j w 2e-7 ln(De / d_ij)
With balanced currents (sum I = 0) the earth-return terms cancel, so the voltage per metre on an
open shield i is E_i = j w 2e-7 sum_k I_k ln(1 / d_ik), d = shield mean radius for its own core.
"""
import cmath
import math
import unittest
from dataclasses import asdict

from pecalc.cablebus import CableBusInput, analyse
from pecalc.impedance import Conductor, open_circuit_voltages

# Three single cables in a flat row ABC, 100 mm centres, shield mean diameter 40 mm (r = 20 mm),
# 1000 A balanced at unity power factor, 60 Hz, 100 m run.
FLAT = dict(voltage_v=15000.0, current_a=1000.0, power_factor=1.0, conductors_per_phase=1, pattern="ABC",
            cable_od_mm=40.0, spacing_mm=100.0, cable_ampacity_a=1200.0, shield_mean_diameter_mm=40.0,
            shield_area_mm2=16.0, length_m=100.0)

# w 2e-7 = 2 pi 60 x 2e-7 = 7.539822e-5 ohm/m
X = 2 * math.pi * 60 * 2e-7
# Middle shield B: E_B = jX [I_A ln(1/s) + I_B ln(1/r) + I_C ln(1/s)] = jX I_B ln(s/r)   (I_A + I_C = -I_B)
#   |E_B| = 7.539822e-5 x 1000 x ln(100/20) = 7.539822e-5 x 1000 x 1.609438 = 0.121349 V/m = 121.349 V/km
E_MID = 0.12134876
# Outer shield A: E_A = jX [I_B ln(r/s) + I_C ln(r/2s)]   (I_A = -(I_B + I_C))
#   ln(r/s) = ln 0.2 = -1.609438, ln(r/2s) = ln 0.1 = -2.302585
#   I_B = 1000 /-120 = (-500, -866.025), I_C = 1000 /+120 = (-500, +866.025)
#   sum = -1.609438 (-500, -866.025) - 2.302585 (-500, 866.025)
#       = (804.719 + 1151.293, 1393.826 - 1994.098) = (1956.012, -600.283) A
#   |sum| = sqrt(1956.012^2 + 600.283^2) = 2046.050 A
#   |E_A| = 7.539822e-5 x 2046.050 = 0.154269 V/m = 154.269 V/km (shield C the same by symmetry)
E_OUT = 0.15426854


class OpenCircuitVoltage(unittest.TestCase):
    def test_go_and_return_pair(self):
        # +I at x=0 and -I at x=300 mm; probe at x=100 mm: E = jX I ln(d2/d1) = jX 500 ln(200/100)
        cs = [Conductor(0, 0, "A", 1e-4, 10), Conductor(300, 0, "B", 1e-4, 10)]
        e = open_circuit_voltages(cs, [500 + 0j, -500 + 0j], [Conductor(100, 0, "P", 0.0, 5)])[0]
        self.assertAlmostEqual(abs(e), X * 500 * math.log(2), places=12)   # 0.0261310 V/m
        self.assertAlmostEqual(cmath.phase(e), math.pi / 2, places=9)


class StandingVoltage(unittest.TestCase):
    def test_flat_hand_check(self):
        r = analyse(CableBusInput(**FLAT, shield_bonding="single_point"))
        sh = r.sheath
        e = {s["label"]: s["e_v_per_km"] for s in sh["shields"]}
        self.assertAlmostEqual(e["S-A00"], E_OUT * 1000, places=2)
        self.assertAlmostEqual(e["S-B01"], E_MID * 1000, places=2)
        self.assertAlmostEqual(e["S-C02"], E_OUT * 1000, places=2)
        # Open-end voltage over the 100 m section: 0.154269 x 100 = 15.43 V on an outer shield.
        self.assertAlmostEqual(sh["standing_v"], 15.43, places=2)
        self.assertEqual(sh["worst_shield"], "S-A00")      # A and C tie; the first one is reported
        self.assertEqual(sh["sections"], 1)
        self.assertIsNone(sh["standing_v_fault"])
        self.assertIsNone(sh["passed"])
        self.assertTrue(any("No verified public limit" in n for n in sh["notes"]))
        self.assertTrue(any("Cross-bonding" in n for n in sh["notes"]))
        self.assertEqual(r.shield_loss_w, 0)

    def test_fault_scales_with_current(self):
        # 20 kA through-fault on a 1000 A rating: x20 -> 15.427 x 20 = 308.54 V
        sh = analyse(CableBusInput(**FLAT, shield_bonding="single_point", fault_ka=20.0)).sheath
        self.assertAlmostEqual(sh["standing_v_fault"], E_OUT * 100 * 20, places=1)

    def test_section_length(self):
        # 25 m minor sections: 0.154269 x 25 = 3.86 V, 4 sections in 100 m
        sh = analyse(CableBusInput(**FLAT, shield_bonding="single_point", shield_section_length_m=25.0)).sheath
        self.assertAlmostEqual(sh["standing_v"], 3.86, places=2)
        self.assertEqual(sh["sections"], 4)
        sh = analyse(CableBusInput(**FLAT, shield_bonding="single_point", shield_section_length_m=30.0)).sheath
        self.assertEqual(sh["sections"], 4)                # ceil(100 / 30)
        for bad in (0.0, -5.0, 150.0):
            with self.assertRaises(ValueError):
                analyse(CableBusInput(**FLAT, shield_bonding="single_point", shield_section_length_m=bad))
        with self.assertRaises(ValueError):
            analyse(CableBusInput(**FLAT, shield_bonding="single_point", shield_voltage_limit_v=0.0))

    def test_limit_pass_and_fail(self):
        ok = analyse(CableBusInput(**FLAT, shield_bonding="single_point", shield_voltage_limit_v=25.0))
        self.assertTrue(ok.sheath["passed"])
        # Longest section within 25 V: 25 / 0.154269 = 162.05 m
        self.assertAlmostEqual(ok.sheath["max_section_m_for_limit"], 162.1, places=1)
        c = ok.checks[-1]
        self.assertIn("standing voltage", c["name"])
        self.assertEqual((c["value"], c["limit"], c["passed"]), (15.43, 25.0, True))
        self.assertIn("favoured", ok.sheath["recommendation"])
        bad = analyse(CableBusInput(**FLAT, shield_bonding="single_point", shield_voltage_limit_v=10.0))
        self.assertFalse(bad.sheath["passed"])
        self.assertFalse(bad.passed)
        self.assertIn("<= 64.8 m", bad.sheath["recommendation"])    # 10 / 0.154269 = 64.82 m

    def test_comparison(self):
        sp = analyse(CableBusInput(**FLAT, shield_bonding="single_point")).sheath["modes"]
        self.assertEqual(sp["single_point"]["shield_loss_w"], 0)
        self.assertGreater(sp["both_ends"]["shield_loss_w"], 0)
        self.assertGreater(sp["both_ends"]["max_lambda1"], 0)
        self.assertLess(sp["both_ends"]["min_ampacity_a"], sp["single_point"]["min_ampacity_a"])
        self.assertIsNone(sp["both_ends"]["standing_v"])

    def test_both_ends_results_unchanged(self):
        # The comparison adds only the `sheath` field and no check: every other field is identical to a run
        # without the bonding comparison, and the both-ends sheath block carries the single-point alternative.
        inp = dict(FLAT, shield_bonding="both_ends", fault_ka=20.0, enclosure_width_mm=500.0, enclosure_height_mm=150.0)
        full = asdict(analyse(CableBusInput(**inp)))
        bare = asdict(analyse(CableBusInput(**inp), compare_bonding=False))
        sh = full.pop("sheath")
        bare.pop("sheath")
        self.assertEqual(full, bare)
        self.assertEqual(sh["modes"]["both_ends"]["shield_loss_w"], full["shield_loss_w"])
        self.assertIsNotNone(sh["standing_v"])
        self.assertFalse(any("standing voltage" in c["name"] for c in full["checks"]))

    def test_enclosure_currents_included(self):
        base = dict(FLAT, shield_bonding="single_point")
        plain = analyse(CableBusInput(**base)).sheath["standing_v"]
        encl = analyse(CableBusInput(**base, enclosure_width_mm=400.0, enclosure_height_mm=120.0)).sheath["standing_v"]
        self.assertNotEqual(plain, encl)
        self.assertLess(abs(encl - plain) / plain, 0.5)

    def test_not_applicable(self):
        self.assertIsNone(analyse(CableBusInput(**dict(FLAT, shield_bonding="none"))).sheath)
        sh = analyse(CableBusInput(**dict(FLAT, shield_bonding="single_point", shield_mean_diameter_mm=None,
                                          shield_area_mm2=None))).sheath
        self.assertIsNone(sh["standing_v"])
        self.assertIsNone(sh["modes"]["both_ends"])
        self.assertIn("not computed", sh["recommendation"])


if __name__ == "__main__":
    unittest.main()
