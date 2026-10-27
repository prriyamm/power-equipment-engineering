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


def _named(result, prefix):
    """The check whose name starts with prefix."""
    return next(c for c in result.checks if c["name"].startswith(prefix))

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
    def test_auto_patterns_are_figure3(self):
        # CSA C22.2 No. 273 Figure 3: 3 arrangements for 2 per phase (all 2 tiers), 5 for 3 per phase.
        self.assertEqual(candidate_patterns(2), ["ABC/CAB", "ABC/BCA", "ABC/CBA"])
        self.assertEqual(candidate_patterns(3, 3), ["ACA/BBB/CAC", "+ABC/BCA./+ABC"])
        self.assertEqual(candidate_patterns(1, 1), ["ABC"])
        with self.assertRaisesRegex(ValueError, "no arrangement of 2 conductors per phase in 1 tier"):
            candidate_patterns(2, 1)
        with self.assertRaisesRegex(ValueError, "covers 1 to 10 conductors per phase"):
            candidate_patterns(11)

    def test_figure3_data(self):
        from pecalc.cablebus import _check_pattern, figure3_match, figure3_patterns
        for n in range(1, 11):
            pats = figure3_patterns(n)
            self.assertGreaterEqual(len(pats), 2)
            for p in pats:
                rows = _check_pattern(p, n, None)            # n of each phase, valid grammar
                self.assertLessEqual(len(rows), 3)            # Clause 4.12.2: 3 layers maximum
                self.assertIsNotNone(figure3_match(p, n))
        # The figure itself lists ABC/BCA beside ABC/CAB: the same groups, mirrored and renamed.
        self.assertEqual(figure3_match("ABC/BCA", 2), "2-1")
        self.assertEqual(figure3_match("BCA", 1), "1-1")           # phase naming
        self.assertEqual(figure3_match(".CABC/BACBA", 3), "3-3")   # mirror image of CBAC./ABCAB
        self.assertIsNone(figure3_match("ABCCBA", 2))                # single row: not in Figure 3
        self.assertIsNone(figure3_match("ABCABCABC", 3))

    def test_pattern_grammar(self):
        from pecalc.cablebus import pattern_positions
        # '+' shifts a tier half a pitch; '.' is an unused position; x starts at 0.
        self.assertEqual(pattern_positions("+A/BC"), [(0.5, 0, "A", 0), (0.0, 1, "B", 0), (1.0, 1, "C", 1)])
        self.assertEqual(pattern_positions(".AB/C.."), [(1.0, 0, "A", 1), (2.0, 0, "B", 2), (0.0, 1, "C", 0)])
        with self.assertRaisesRegex(ValueError, "optional leading"):
            pattern_positions("AB+C")

    def test_staggered_layout(self):
        r = analyse(CableBusInput(voltage_v=600, current_a=1500, conductors_per_phase=3, size="750",
                                  pattern="+ABCA/BCABC"))
        top = sorted(c.x_mm for c in r.conductors if c.tier == 0)
        bottom = sorted(c.x_mm for c in r.conductors if c.tier == 1)
        self.assertAlmostEqual(top[0], round(r.pitch_mm / 2, 1), delta=0.06)
        self.assertAlmostEqual(bottom[0], 0.0)
        self.assertEqual(len(top) + len(bottom), 9)
        self.assertTrue(_named(r, "Phase arrangement")["passed"])

    def test_pattern_outside_figure3_fails_the_check(self):
        # 4 x 750 kcmil per phase in 4 tiers: a valid layout, but not a Figure 3 arrangement.
        r = analyse(CableBusInput(voltage_v=600, current_a=2000, conductors_per_phase=4, size="750",
                                  pattern="ABC/ABC/ABC/ABC", enclosure_width_mm=500, enclosure_height_mm=500))
        self.assertEqual(len(r.conductors), 12)
        self.assertEqual(sorted({c.tier for c in r.conductors}), [0, 1, 2, 3])
        self.assertAlmostEqual(sum(c.current_a for c in r.conductors if c.phase == "A"), 2000, delta=0.5)
        c = _named(r, "Phase arrangement")
        self.assertFalse(c["passed"])
        self.assertIn("4.12.4", c["note"])
        self.assertFalse(r.passed)
        with self.assertRaisesRegex(ValueError, "no arrangement of 8 conductors per phase in 4 tier"):
            analyse(CableBusInput(voltage_v=600, conductors_per_phase=8, tiers=4))

    def test_auto_skips_arrangements_that_do_not_fit(self):
        # 3 tiers of 750 kcmil (OD ~ 29 mm, pitch ~ 59 mm) are ~ 147 mm high: a 120 mm enclosure takes 2 tiers.
        r = analyse(CableBusInput(voltage_v=600, current_a=3000, conductors_per_phase=4, size="750",
                                  enclosure_width_mm=800, enclosure_height_mm=120))
        self.assertEqual(r.input.tiers, 2)
        self.assertTrue(all(p.pattern.count("/") == 1 for p in r.patterns_compared))
        with self.assertRaisesRegex(ValueError, "No CSA 273 Figure 3 arrangement"):
            analyse(CableBusInput(voltage_v=600, current_a=3000, conductors_per_phase=4, size="750",
                                  enclosure_width_mm=800, enclosure_height_mm=60))

    def test_reference_concept_4000a(self):
        # Reference design: 4000 A, 600 V, 6 x 750 kcmil Cu per phase.
        r = analyse(CableBusInput(voltage_v=600, current_a=4000, conductors_per_phase=6, tiers=2, size="750"))
        # Changed by the review fixes: the termination check now uses NEC Table 310.16 (raceway) at the derived
        # 75 C rating (475 A for 750 kcmil Cu), not the free-air table, so the 724 A worst conductor fails it.
        # Every other check (free-air ampacity, spacing, voltage drop) still passes.
        self.assertEqual([c["name"] for c in r.checks if not c["passed"]],
                         ["Most heavily loaded conductor within termination rating"])
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


class CableBusVoltageDrop(unittest.TestCase):
    def test_hand_check_balanced_trefoil(self):
        # Balanced trefoil, one conductor per phase, side s = 100 mm, GMR 10 mm, R = 0.05 ohm/km,
        # 480 V, 1000 A at pf 0.8 lagging, 60 m. By symmetry each phase sees
        #   dV_p = I_p (z_self - z_mutual) L = I_p (R + j w 2e-7 ln(s / GMR)) L
        # (the Carson earth-return terms cancel because Ia + Ib + Ic = 0).
        #   X = 2 pi 60 x 2e-7 x ln(10) = 1.73611e-4 ohm/m
        #   I = 1000 /-36.87 deg = 800 - j600 A
        #   dV = (800 - j600)(5e-5 + j1.73611e-4) x 60 = 8.6500 + j6.5333 V
        #   Vs = 480 / sqrt 3 = 277.128 V (phase A at 0 deg)
        #   |Vs - dV| = |268.478 - j6.533| = 268.558 V
        #   exact  = (277.128 - 268.558) / 277.128 = 3.0926 %
        #   approx = I L (R cos phi + X sin phi) / Vs = 8.6500 / 277.128 = 3.1213 %
        # Every phase gives the same value because each is measured against its own source voltage.
        from pecalc.cablebus import phase_voltage_drops
        h = 100 * math.sqrt(3) / 2
        cs = [Conductor(0, 0, "A", 5e-5, 10), Conductor(100, 0, "B", 5e-5, 10), Conductor(50, h, "C", 5e-5, 10)]
        res = solve_sharing(cs, balanced_three_phase(1000, 0.8))
        vd = phase_voltage_drops(res, 480, 0.8, 60)
        for p in "ABC":
            self.assertAlmostEqual(vd[p][0], 3.0926, places=3)
            self.assertAlmostEqual(vd[p][1], 3.1213, places=3)

    def test_invariant_to_phase_labelling(self):
        # Cyclic relabelling (A->B->C->A) is the same physical bus; only the names change.
        # Before the fix, flat ABC / BCA / CAB gave 4.29 / 2.14 / 2.94 %.
        for kw, patterns in (
                (dict(current_a=600, conductors_per_phase=1, length_m=150), ("ABC", "BCA", "CAB")),
                (dict(current_a=1200, conductors_per_phase=2, length_m=100), ("ABCCBA", "BCAACB", "CABBAC"))):
            vds = [analyse(CableBusInput(voltage_v=600, size="750", pattern=p, **kw)).vd_pct for p in patterns]
            for v in vds[1:]:
                self.assertAlmostEqual(v, vds[0], places=6)
        self.assertAlmostEqual(analyse(CableBusInput(voltage_v=600, size="750", pattern="BCA", current_a=600,
                                                     conductors_per_phase=1, length_m=150)).vd_pct, 4.292, places=2)

    def test_invariant_with_shields_bonded_both_ends(self):
        base = dict(voltage_v=15000, current_a=2000, conductors_per_phase=2, size="750", cable_od_mm=45,
                    cable_ampacity_a=900, shield_area_mm2=16, shield_mean_diameter_mm=38, shield_bonding="both_ends")
        vds = [analyse(CableBusInput(**base, pattern=p)).vd_pct for p in ("ABCCBA", "BCAACB", "CABBAC")]
        self.assertAlmostEqual(vds[1], vds[0], places=6)
        self.assertAlmostEqual(vds[2], vds[0], places=6)


class DatasheetShieldDerating(unittest.TestCase):
    BASE = dict(voltage_v=15000, current_a=2000, conductors_per_phase=3, size="750", cable_od_mm=45,
                cable_ampacity_a=900, shield_area_mm2=16, shield_mean_diameter_mm=38)

    def test_factor_hand_values(self):
        from pecalc.cablebus import datasheet_shield_derating as k
        self.assertEqual(k(0.0, 0.0), 1.0)                       # no shield loss: no change
        self.assertAlmostEqual(k(0.21, 0.0), 1 / 1.1, places=9)  # sqrt(1 / 1.21) = 0.90909
        self.assertAlmostEqual(k(0.21, 0.1), math.sqrt(1.1 / 1.21), places=9)  # = 0.95346
        self.assertEqual(k(0.0, 0.2), 1.0)                       # never raises a datasheet rating

    def test_single_point_bonding_is_not_derated(self):
        r = analyse(CableBusInput(**self.BASE, shield_bonding="single_point"))
        self.assertTrue(all(c.ampacity_a == 900.0 for c in r.conductors))
        self.assertNotIn("shield derating", r.ampacity_basis)

    def test_both_ends_bonding_derates_by_own_lambda1(self):
        from pecalc.cablebus import datasheet_shield_derating
        # A flat single row (not a Figure 3 arrangement) has a large enough shield loss to exceed 10 %.
        r = analyse(CableBusInput(**self.BASE, shield_bonding="both_ends", pattern="ABCCBAABC"))
        self.assertLess(max(c.ampacity_a for c in r.conductors), 900.0)
        lam = float(r.ampacity_basis.split("lambda1 ")[1].split()[0])
        worst = max(r.conductors, key=lambda c: c.loading_pct)
        self.assertAlmostEqual(worst.ampacity_a, 900 * datasheet_shield_derating(lam), delta=0.2)
        self.assertTrue(any(n.startswith("WARNING: shield circulating current") for n in r.notes))
        # A datasheet that already assumes the same loss is not derated again.
        same = analyse(CableBusInput(**self.BASE, shield_bonding="both_ends", cable_ampacity_lambda1_ref=10.0))
        self.assertTrue(all(c.ampacity_a == 900.0 for c in same.conductors))


if __name__ == "__main__":
    unittest.main()


class CalculatedAmpacity(unittest.TestCase):
    def _lv(self, size):
        from pecalc.thermal import CableConstruction
        return CableConstruction(size, insulation="XHHW", insulation_mm=cond.insulation_mm(size))

    def test_lv_calculated_is_somewhat_above_nec_free_air_table(self):
        # NEC Table 310.17 is known to be conservative relative to IEC 60287 for an
        # isolated cable; expect the calculated value 10-35 % higher at 30 C.
        from pecalc.thermal import free_air_ampacity
        for size in ("1/0", "4/0", "500", "750", "1000"):
            with self.subTest(size=size):
                calc = free_air_ampacity(self._lv(size), 30).ampacity_a
                table = amp.table_ampacity("NEC", "free_air", "Cu", size, 90)
                self.assertTrue(1.10 <= calc / table <= 1.35, calc / table)

    def test_ambient_and_shield_loss_reduce_ampacity(self):
        from pecalc.thermal import free_air_ampacity
        c = self._lv("500")
        a30 = free_air_ampacity(c, 30).ampacity_a
        a40 = free_air_ampacity(c, 40).ampacity_a
        a40_l = free_air_ampacity(c, 40, lambda1=0.3).ampacity_a
        self.assertGreater(a30, a40)
        self.assertGreater(a40, a40_l)
        self.assertEqual(free_air_ampacity(c, 95).ampacity_a, 0)

    def test_dielectric_loss_scales_with_voltage(self):
        from pecalc.thermal import CableConstruction, dielectric_loss
        mv = CableConstruction("750", insulation="EPR", insulation_mm=7.2, voltage_v=15000)
        lv = CableConstruction("750", insulation="EPR", insulation_mm=7.2, voltage_v=600)
        self.assertAlmostEqual(dielectric_loss(mv) / dielectric_loss(lv), (15000 / 600) ** 2, places=6)


class CableBusCalculatedMV(unittest.TestCase):
    BASE = dict(voltage_v=15000, current_a=2000, size="750", insulation="EPR", insulation_mm=7.2,
                shield_mm=0.13, jacket_mm=2.0, length_m=60)

    def test_two_per_phase_fails_three_passes(self):
        two = analyse(CableBusInput(**self.BASE, conductors_per_phase=2, shield_bonding="single_point"))
        three = analyse(CableBusInput(**self.BASE, conductors_per_phase=3, shield_bonding="single_point"))
        self.assertFalse(two.passed)
        self.assertTrue(three.passed)

    def test_both_ends_bonding_derates_each_cable(self):
        sp = analyse(CableBusInput(**self.BASE, conductors_per_phase=3, shield_bonding="single_point"))
        be = analyse(CableBusInput(**self.BASE, conductors_per_phase=3, shield_bonding="both_ends"))
        self.assertLess(min(c.ampacity_a for c in be.conductors), min(c.ampacity_a for c in sp.conductors))
        self.assertGreater(be.max_loading_pct, sp.max_loading_pct)


class Lugs(unittest.TestCase):
    def test_default_terminal_temperature_rule(self):
        from pecalc.lugs import default_terminal_temp
        # NEC 110.14(C)(1) / CEC 4-006: <= 100 A or 14-1 AWG -> 60 C; otherwise 75 C.
        self.assertEqual(default_terminal_temp("NEC", 90, "4")[0], 60)
        self.assertEqual(default_terminal_temp("NEC", 400, "500")[0], 75)
        self.assertEqual(default_terminal_temp("CEC", 400, "1")[0], 60)

    def test_quantities_and_pad_capacity(self):
        from pecalc.lugs import LugInput, select_lugs
        r = select_lugs(LugInput(size="500", sets_per_phase=4, circuit_current_a=1600, neutral=True,
                                 ground_size="3/0", pad_positions=2))
        self.assertEqual(r.total_lugs, 3 * 4 + 4 + 4)
        self.assertTrue(r.passed)
        r = select_lugs(LugInput(size="750", sets_per_phase=6, circuit_current_a=4000, pad_positions=2))
        self.assertFalse(r.passed)

    def test_style_by_size_and_termination(self):
        from pecalc.lugs import LugInput, select_lugs
        big = select_lugs(LugInput(size="250", circuit_current_a=255)).lines[0]
        small = select_lugs(LugInput(size="6", circuit_current_a=65)).lines[0]
        brk = select_lugs(LugInput(size="250", circuit_current_a=255, termination="breaker")).lines[0]
        self.assertIn("2-hole", big.style)
        self.assertEqual(big.hole_spacing_in, "1-3/4")
        self.assertIn("1-hole", small.style)
        self.assertIn("mechanical", brk.style)

    def test_feeder_includes_lug_schedule(self):
        r = size_feeder(FeederInput(voltage_v=480, continuous_a=400, length_m=30.48))
        self.assertEqual(r.lugs.lines[0].quantity, 3 * r.recommended.sets)


class MagneticField(unittest.TestCase):
    def test_single_conductor_ampere_law(self):
        from pecalc.field import b_rms_ut
        # B = mu0 I / (2 pi r): 1000 A at 1 m = 200 uT.
        self.assertAlmostEqual(b_rms_ut([Conductor(0, 0, "A", 1e-4, 5)], [1000], 0, 1000), 200.0, places=6)

    def test_flat_three_phase_far_field(self):
        from pecalc.field import b_rms_ut, far_field_flat_ut
        g = balanced_three_phase(1000, 1.0)
        cs = [Conductor(-100, 0, "A", 1e-4, 5), Conductor(0, 0, "B", 1e-4, 5), Conductor(100, 0, "C", 1e-4, 5)]
        cur = [g[p].current for p in "ABC"]
        self.assertAlmostEqual(b_rms_ut(cs, cur, 0, 5000) / far_field_flat_ut(1000, 0.1, 5), 1, delta=0.01)


class Enclosure(unittest.TestCase):
    BASE = dict(voltage_v=600, current_a=4000, conductors_per_phase=6, tiers=2, size="750", length_m=61)

    def test_enclosure_carries_induced_current_and_loss(self):
        r = analyse(CableBusInput(**self.BASE, enclosure_width_mm=560, enclosure_height_mm=200))
        self.assertGreater(r.enclosure_loss_w, 0)
        self.assertGreater(r.enclosure_current_a, 0)
        self.assertLess(r.enclosure_loss_w, 0.2 * r.conductor_loss_w)

    def test_enclosure_too_small_is_rejected(self):
        with self.assertRaises(ValueError):
            analyse(CableBusInput(**self.BASE, enclosure_width_mm=200, enclosure_height_mm=200))

    def test_no_enclosure_reports_zero(self):
        r = analyse(CableBusInput(**self.BASE))
        self.assertEqual(r.enclosure_loss_w, 0)
        self.assertIn("side 1 m", r.field_ut)


class SwitchgearBus(unittest.TestCase):
    def test_single_bar_rating_matches_din_43671_order(self):
        # DIN 43671 (memory, UNVERIFIED): 100 x 10 mm Cu, 35 C ambient, 30 K rise, AC:
        # bare ~1600-1700 A, painted ~1800-1900 A. Loose +/-15 % band.
        from pecalc.switchgear import BusInput, analyse_bus
        base = dict(bar_thickness_mm=10, bar_width_mm=100, bars_per_phase=1, phase_spacing_mm=200,
                    ambient_c=35, max_rise_c=30, current_a=1500)
        bare = analyse_bus(BusInput(**base, finish="bare")).rated_current_at_limit_a
        painted = analyse_bus(BusInput(**base, finish="painted")).rated_current_at_limit_a
        self.assertAlmostEqual(bare / 1650, 1, delta=0.15)
        self.assertAlmostEqual(painted / 1850, 1, delta=0.15)
        self.assertGreater(painted, bare)

    def test_fault_force_matches_classic_phase_pack_formula(self):
        from pecalc.forces import peak_factor
        from pecalc.switchgear import BusInput, analyse_bus
        r = analyse_bus(BusInput(bars_per_phase=1, phase_spacing_mm=300, fault_ka=50, x_over_r=15))
        classic = 0.866 * 2e-7 * (peak_factor(15) * 50e3) ** 2 / 0.3
        self.assertAlmostEqual(r.peak_force_n_per_m / classic, 1, delta=0.05)

    def test_edge_to_edge_is_stiffer_against_phase_forces(self):
        from pecalc.switchgear import BusInput, analyse_bus
        f2f = analyse_bus(BusInput(fault_ka=65, support_span_m=0.6))
        e2e = analyse_bus(BusInput(fault_ka=65, support_span_m=0.6, orientation="edge_to_edge"))
        self.assertGreater(f2f.bending_stress_mpa, 5 * e2e.bending_stress_mpa)
        self.assertGreater(e2e.max_span_m, f2f.max_span_m)

    def test_ac_resistance_ratio_and_lamination_sharing(self):
        from pecalc.switchgear import BusInput, analyse_bus
        r = analyse_bus(BusInput(bars_per_phase=2))
        self.assertTrue(1.0 < r.rac_over_rdc < 1.6)
        self.assertAlmostEqual(sum(r.lamination_share_pct) / 2, 100, delta=3)


class Transformer(unittest.TestCase):
    def _r(self, **kw):
        from pecalc.transformer import TransformerInput, design
        return design(TransformerInput(**kw))

    def test_emf_equation_and_turns_ratio(self):
        from pecalc.transformer import TransformerInput
        inp = TransformerInput(kva=1500, hv_v=13800, lv_v=480)
        r = self._r(kva=1500, hv_v=13800, lv_v=480)
        d = r.design
        # E = 4.44 f N Bm Ai
        et = 4.44 * 60 * d["b_max_t"] * d["core_area_net_cm2"] / 1e4
        self.assertAlmostEqual(et / d["volts_per_turn"], 1, delta=0.005)
        # Delta HV / wye LV phase-voltage ratio within one turn
        ratio = 13800 / (480 / math.sqrt(3))
        self.assertLessEqual(abs(d["turns_hv"] - d["turns_lv"] * ratio), 1)

    def test_rogowski_factor(self):
        from pecalc.transformer import rogowski_factor
        self.assertAlmostEqual(rogowski_factor(10, 1), 1 - 1 / (10 * math.pi), places=6)
        self.assertLess(rogowski_factor(1, 1), rogowski_factor(5, 1))

    def test_efficiency_and_fault_current_identities(self):
        r = self._r(kva=1500, hv_v=13800, lv_v=480, power_factor=1.0)
        nll, ll = r.losses["no_load_w"], r.losses["load_loss_w"]
        self.assertAlmostEqual(r.performance["efficiency_pct"]["100%"], 1.5e6 / (1.5e6 + nll + ll) * 100, places=2)
        self.assertAlmostEqual(r.performance["max_efficiency_load_pct"], math.sqrt(nll / ll) * 100, delta=0.1)
        i_fl = 1.5e6 / (math.sqrt(3) * 480)
        self.assertAlmostEqual(r.short_circuit["lv_fault_ka_rms"], i_fl / (r.impedance["z_pct"] / 100) / 1000,
                               delta=0.05)

    def test_typical_1500kva_liquid_losses_in_industry_range(self):
        # Typical 1500 kVA, 15 kV class liquid-filled distribution transformer (industry practice,
        # UNVERIFIED band): no-load 1-3 kW, load loss 8-20 kW, %Z 4-7.
        r = self._r(kva=1500, hv_v=13800, lv_v=480)
        self.assertTrue(1000 <= r.losses["no_load_w"] <= 3000)
        self.assertTrue(8000 <= r.losses["load_loss_w"] <= 20000)
        self.assertTrue(4 <= r.impedance["z_pct"] <= 7)

    def test_impedance_tuning_hits_target(self):
        from pecalc.transformer import TransformerInput, design_for_impedance
        r = design_for_impedance(TransformerInput(kva=1500, hv_v=13800, lv_v=480, target_z_pct=5.75))
        self.assertAlmostEqual(r.impedance["z_pct"], 5.75, delta=0.05)

    def test_standard_kva_selection(self):
        from pecalc.transformer import next_standard_kva
        self.assertEqual(next_standard_kva(1180, 1.25), 1500)
        self.assertEqual(next_standard_kva(300), 300)


class CasesAndReports(unittest.TestCase):
    EXAMPLES = __import__("pathlib").Path(__file__).resolve().parents[2] / "examples"

    def test_all_examples_run_and_render(self):
        from pecalc.cases import Case
        from pecalc.report import render
        files = sorted(self.EXAMPLES.glob("*.json"))
        self.assertGreaterEqual(len(files), 4)
        for f in files:
            with self.subTest(case=f.name):
                case = Case.load(f)
                html_doc = render(case, case.run())
                self.assertIn("<h2>Checks</h2>", html_doc)
                self.assertIn(case.input_hash(), html_doc)

    def test_unknown_input_is_rejected(self):
        from pecalc.cases import Case
        with self.assertRaises(ValueError):
            Case(module="feeder", inputs={"voltage": 480}).input_object()

    def test_input_hash_changes_with_inputs(self):
        from pecalc.cases import Case
        a = Case(module="feeder", inputs={"voltage_v": 480, "continuous_a": 400})
        b = Case(module="feeder", inputs={"voltage_v": 480, "continuous_a": 401})
        self.assertNotEqual(a.input_hash(), b.input_hash())


class CableBusDesigner(unittest.TestCase):
    def test_lv_options_pass_and_fit_enclosures(self):
        from pecalc.cablebus_design import INCH, DesignRequest, design_options
        r = design_options(DesignRequest(voltage_v=600, current_a=4000))
        passing = [o for o in r.options if o.passed]
        self.assertGreaterEqual(len(passing), 3)
        from pecalc.cablebus import figure3_match, pattern_positions
        for o in passing:
            self.assertLessEqual(o.max_loading_pct, 95.0)
            self.assertIsNotNone(figure3_match(o.pattern, o.per_phase))
            span = max(x for x, *_ in pattern_positions(o.pattern))
            needed_w = span * 2 * o.cable_od_mm + o.cable_od_mm + 2 * 25
            self.assertGreaterEqual(o.inside_w_mm + 2.0, needed_w)  # OD is reported rounded
        tags = {t for o in r.options for t in o.tags}
        self.assertTrue({"least copper", "smallest enclosure", "most margin"} <= tags)

    def test_designer_uses_figure3_tiers_only(self):
        from pecalc.cablebus_design import DesignRequest, design_options
        # Figure 3 has no 4-tier arrangement, so tier option 4 adds nothing; 1 tier exists only for 1 per phase.
        self.assertEqual(DesignRequest().tier_options, (1, 2, 3, 4))
        r = design_options(DesignRequest(voltage_v=600, current_a=4000, top_n=30))
        self.assertTrue(r.options)
        self.assertTrue(all(o.tiers in (2, 3) for o in r.options))
        r2 = design_options(DesignRequest(voltage_v=600, current_a=4000, tier_options=(2,)))
        self.assertTrue(r2.options)
        self.assertTrue(all(o.tiers == 2 for o in r2.options))
        # Beyond 10 per phase Figure 3 has no arrangement: the size is skipped with a note.
        r3 = design_options(DesignRequest(voltage_v=600, current_a=4500, sizes=("500",)))   # 12 x 380 A
        self.assertTrue(any("Figure 3 covers 1 to 10" in n for n in r3.notes))

    def test_more_tiers_gives_narrower_enclosure(self):
        from pecalc.cablebus_design import DesignRequest, design_options
        # 2000 A (was 4000 A): with the termination limit now taken from Table 310.16 (380 A per 500 kcmil
        # conductor at 75 C), 4000 A needs 11+ per phase, beyond Figure 3.
        r = design_options(DesignRequest(voltage_v=600, current_a=2000, sizes=("500",), top_n=20))
        widths = {}
        for o in r.options:
            widths.setdefault(o.per_phase, {})[o.tiers] = o.inside_w_mm
        pairs = [w for w in widths.values() if 2 in w and 3 in w]
        self.assertTrue(pairs, "expected a design available in 2 and in 3 tiers")
        for w in pairs:
            self.assertLess(w[3], w[2])

    def test_mv_needs_construction_and_checks_blocks(self):
        from pecalc.cablebus_design import DesignRequest, design_options
        with self.assertRaises(ValueError):
            design_options(DesignRequest(voltage_v=15000, current_a=2000))
        r = design_options(DesignRequest(voltage_v=15000, current_a=2000, insulation="EPR", insulation_mm=7.2,
                                         shield_mm=0.13, jacket_mm=2.0, fault_ka=40))
        self.assertTrue(any(o.passed for o in r.options))
        self.assertTrue(all(o.block_stress_mpa is not None for o in r.options))

    def test_tested_block_rating_can_fail_a_design(self):
        from pecalc.cablebus_design import DesignRequest, design_options
        r = design_options(DesignRequest(voltage_v=600, current_a=4000, fault_ka=100, x_over_r=30,
                                         block_rated_load_n=500))
        self.assertTrue(any("rated" in " ".join(o.failed_checks) for o in r.options))

    def test_drawing_svg(self):
        from pecalc.cablebus import CableBusInput, analyse
        from pecalc.drawing import cablebus_svg
        inp = CableBusInput(voltage_v=600, current_a=3000, conductors_per_phase=4, tiers=2, size="750",
                            enclosure_width_mm=457.2, enclosure_height_mm=203.2)
        svg = cablebus_svg(inp, analyse(inp))
        self.assertTrue(svg.startswith("<svg"))
        self.assertEqual(svg.count("<circle") - 3, 12)   # 12 cables + 3 legend dots
        self.assertIn("GPO-3", svg)
