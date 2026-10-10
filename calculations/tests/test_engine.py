"""Engine tests against independent references.

Each test states its reference. Values from code books are marked where they
were entered from memory and still need checking against the licensed copy.
"""

import math
import unittest

from pecalc import ampacity as amp
from pecalc import conductors as cond
from pecalc.cablebus import CableBusInput, analyse, candidate_patterns
from pecalc.forces import fault_forces, peak_factor
from pecalc.impedance import Conductor, balanced_three_phase, solve_sharing
from pecalc.sizing import FeederInput, size_feeder

OHM_KFT = 1000 * cond.FT  # ohm/m -> ohm/1000 ft


class ConductorPhysics(unittest.TestCase):
    # NEC Chapter 9 Table 8, DC resistance at 75 C, ohm/kft (uncoated Cu, Al).
    TABLE8 = {("14", "Cu"): 3.14, ("1/0", "Cu"): 0.122, ("4/0", "Cu"): 0.0608, ("500", "Cu"): 0.0258,
              ("1000", "Cu"): 0.0129, ("1/0", "Al"): 0.201, ("500", "Al"): 0.0424}

    def test_dc_resistance_matches_nec_table8(self):
        for (size, mat), ref in self.TABLE8.items():
            with self.subTest(size=size, mat=mat):
                self.assertAlmostEqual(cond.rdc_ohm_per_m(size, mat) * OHM_KFT / ref, 1, delta=0.01)

    def test_ac_resistance_500_cu_close_to_table9(self):
        # NEC Ch. 9 Table 9: 500 kcmil Cu, PVC conduit, AC R = 0.027 ohm/kft.
        rac = cond.rac_ohm_per_m("500", "Cu", spacing_mm=cond.cable_od_mm("500")) * OHM_KFT
        self.assertAlmostEqual(rac, 0.027, delta=0.0015)

    def test_size_parsing(self):
        self.assertEqual(cond.normalize_size("500 kcmil"), "500")
        self.assertEqual(cond.normalize_size("#2"), "2")
        with self.assertRaises(ValueError):
            cond.normalize_size("123")


class CorrectionFactors(unittest.TestCase):
    def test_ambient_equation_matches_published_rounded_factors(self):
        # NEC Table 310.15(B)(1): 90 C column at 40 C = 0.91, 75 C column at 40 C = 0.88.
        self.assertAlmostEqual(amp.ambient_factor(40, 90), 0.91, delta=0.005)
        self.assertAlmostEqual(amp.ambient_factor(40, 75), 0.88, delta=0.005)
        self.assertEqual(amp.ambient_factor(95, 90), 0)

    def test_grouping_factors(self):
        self.assertEqual(amp.ccc_factor("NEC", 3), 1.0)
        self.assertEqual(amp.ccc_factor("NEC", 6), 0.8)
        self.assertEqual(amp.ccc_factor("NEC", 9), 0.7)
        self.assertEqual(amp.ccc_factor("CEC", 24), 0.7)

    def test_cec_placeholder_is_refused(self):
        with self.assertRaises(amp.DataStatusError):
            size_feeder(FeederInput(code="CEC", continuous_a=100))


class FeederSizing(unittest.TestCase):
    def test_hand_example_single_set(self):
        # 400 A continuous -> 500 A at 75 C terminals. NEC 310.16 75 C: 900 kcmil = 520 A,
        # 800 kcmil = 490 A (too small). Hand calculation.
        r = size_feeder(FeederInput(voltage_v=480, continuous_a=400, length_m=30.48, sets=1))
        self.assertEqual(r.recommended.size, "900")

    def test_hand_example_two_sets(self):
        # 2 sets: 250 A per set at 75 C -> 250 kcmil (255 A).
        r = size_feeder(FeederInput(voltage_v=480, continuous_a=400, length_m=30.48, sets=2))
        self.assertEqual(r.recommended.size, "250")

    def test_parallel_minimum_enforced(self):
        r = size_feeder(FeederInput(voltage_v=480, continuous_a=100, length_m=10, sets=2))
        self.assertGreaterEqual(cond.size_index(r.recommended.size), cond.size_index("1/0"))

    def test_voltage_drop_simple_formula(self):
        # VD = sqrt(3) I L (R cos + X sin); compare with an independent re-computation.
        inp = FeederInput(voltage_v=480, continuous_a=200, length_m=100, sets=1, power_factor=1.0)
        r = size_feeder(inp).recommended
        expected = math.sqrt(3) * 200 * 100 * r.r_ohm_per_km / 1000 / 480 * 100
        self.assertAlmostEqual(r.vd_pct, expected, delta=0.01)


class ImpedanceAndSharing(unittest.TestCase):
    def _flat(self, pattern, size="750"):
        r = cond.rac_ohm_per_m(size, "Cu", 90)
        g = cond.gmr_mm(size)
        p = 2 * cond.cable_od_mm(size)
        return [Conductor(i * p, 0, ph, r, g) for i, ph in enumerate(pattern)], p, r

    def test_trefoil_reactance_equals_closed_form(self):
        size = "500"
        r = cond.rac_ohm_per_m(size, "Cu", 90)
        g = cond.gmr_mm(size)
        s = 60.0
        cs = [Conductor(0, 0, "A", r, g), Conductor(s, 0, "B", r, g), Conductor(s / 2, s * math.sqrt(3) / 2, "C", r, g)]
        res = solve_sharing(cs, balanced_three_phase(1000, 1.0))
        z = res.group_drop_v_per_m["A"] / res.groups["A"].current
        self.assertAlmostEqual(z.imag, cond.reactance_ohm_per_m(size, s), places=9)
        self.assertAlmostEqual(z.real, r, places=9)

    def test_mirrored_arrangement_shares_equally(self):
        cs, _, _ = self._flat("ABCCBA")
        res = solve_sharing(cs, balanced_three_phase(1500, 0.9))
        for i in range(6):
            self.assertAlmostEqual(res.share_pct(i), 100, delta=0.1)

    def test_sequential_arrangement_is_unbalanced(self):
        cs, _, _ = self._flat("ABCABC")
        res = solve_sharing(cs, balanced_three_phase(1500, 0.9))
        self.assertGreater(max(res.share_pct(i) for i in range(6)), 110)

    def test_phase_currents_sum_to_given_total(self):
        cs, _, _ = self._flat("ABCABCABC")
        groups = balanced_three_phase(2000, 0.85)
        res = solve_sharing(cs, groups)
        for ph in "ABC":
            total = sum(res.currents[i] for i in res.group_members(ph))
            self.assertAlmostEqual(abs(total - groups[ph].current), 0, places=6)


class Forces(unittest.TestCase):
    def test_flat_three_phase_matches_classic_formula(self):
        # Middle conductor of a flat 3-phase bus: F = 0.866 x 2e-7 x ip^2 / d (IEEE 605 / IEC 60865 basis).
        cs = [Conductor(0, 0, "A", 1e-4, 5), Conductor(300, 0, "B", 1e-4, 5), Conductor(600, 0, "C", 1e-4, 5)]
        r = fault_forces(cs, {0: 1, 1: 1, 2: 1}, 50, 15)
        ip = peak_factor(15) * 50e3
        self.assertEqual(r.worst_index, 1)
        self.assertAlmostEqual(r.worst_n_per_m / (0.866 * 2e-7 * ip ** 2 / 0.3), 1, delta=0.02)

    def test_asymmetric_peak_100ka_xr30(self):
        # Cable bus maker literature: 100 kA rms sym -> 255-270 kA first asymmetric peak.
        cs = [Conductor(0, 0, "A", 1e-4, 5), Conductor(300, 0, "B", 1e-4, 5), Conductor(600, 0, "C", 1e-4, 5)]
        r = fault_forces(cs, {0: 1, 1: 1, 2: 1}, 100, 30)
        self.assertTrue(255 <= r.peak_current_ka <= 272)


class CableBus(unittest.TestCase):
    def test_patterns_generated(self):
        self.assertIn("ABCCBA", candidate_patterns(2, 1))
        with self.assertRaises(ValueError):
            candidate_patterns(2, 4)

    def test_reference_concept_4000a(self):
        # Reference design: 4000 A, 600 V, 6 x 750 kcmil Cu per phase.
        r = analyse(CableBusInput(voltage_v=600, current_a=4000, conductors_per_phase=6, tiers=2, size="750"))
        self.assertTrue(r.passed)
        # Unequal sharing makes the worst conductor carry more than the 666.7 A equal share.
        self.assertGreater(max(c.current_a for c in r.conductors), 4000 / 6)

    def test_mv_requires_datasheet_inputs(self):
        with self.assertRaises(ValueError):
            analyse(CableBusInput(voltage_v=15000, current_a=2000, conductors_per_phase=2))

    def test_both_ends_bonding_adds_shield_loss(self):
        base = dict(voltage_v=15000, current_a=2000, conductors_per_phase=3, size="750", cable_od_mm=45,
                    cable_ampacity_a=900, shield_area_mm2=16, shield_mean_diameter_mm=38)
        single = analyse(CableBusInput(**base, shield_bonding="single_point"))
        both = analyse(CableBusInput(**base, shield_bonding="both_ends"))
        self.assertEqual(single.shield_loss_w, 0)
        self.assertGreater(both.shield_loss_w, 0)
        self.assertGreater(both.shield_current_a, 0)


if __name__ == "__main__":
    unittest.main()
