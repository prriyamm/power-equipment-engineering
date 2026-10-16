"""DOE 10 CFR 431.196 minimum-efficiency check (pecalc.transformer.doe_efficiency_check).

Hand checks work from no-load loss P0 and load loss Pk (at the Appendix A reference temperature) to the
efficiency at the Appendix A per-unit load L, on the unity power factor output basis of Appendix A 5.1-5.3:
    eta = L S / (L S + P0 + L^2 Pk) x 100
and compare it with the table minimum read from the eCFR (data/doe_10cfr431_efficiency.json).
"""

import unittest

from pecalc.transformer import (DOE_CHECK_NAME, DOE_DATA, TransformerInput, design, doe_category,
                                doe_efficiency_check)


def eta(kva, load, p0, pk):
    s = kva * 1000
    return load * s / (load * s + p0 + load ** 2 * pk) * 100


class HandChecks(unittest.TestCase):
    def test_liquid_three_phase_1000kva(self):
        # 1000 kVA liquid-immersed, 50 % load: out = 0.5 x 1,000,000 = 500,000 W.
        # Design A: P0 1000 W, Pk(55 C) 8000 W -> losses 1000 + 0.25 x 8000 = 3000 W
        #   eta = 500,000 / 503,000 = 99.40358 %  < Table 5 1000 kVA 99.43 %  -> fail, margin -0.0264
        e = eta(1000, 0.5, 1000, 8000)
        self.assertAlmostEqual(e, 99.40358, places=4)
        r = doe_efficiency_check("liquid", 3, 1000, efficiency_pct=e, date="2020-06-01")
        self.assertEqual(r["window"]["id"], "(b)(2)")
        self.assertEqual(r["required_pct"], 99.43)
        self.assertEqual(r["status"], "fail")
        self.assertAlmostEqual(r["margin_pct"], -0.02642, places=4)
        # Design B: P0 700 W, Pk 6000 W -> 700 + 1500 = 2200 W; eta = 500,000 / 502,200 = 99.56193 % >= 99.43
        e = eta(1000, 0.5, 700, 6000)
        self.assertAlmostEqual(e, 99.56193, places=4)
        self.assertEqual(doe_efficiency_check("liquid", 3, 1000, efficiency_pct=e, date="2020-06-01")["status"], "pass")
        # Same unit after 2029-04-23 (Table 6, 1000 kVA 99.46 %): still passes.
        r = doe_efficiency_check("liquid", 3, 1000, efficiency_pct=e, date="2029-04-23")
        self.assertEqual((r["window"]["id"], r["required_pct"], r["status"]), ("(b)(3)", 99.46, "pass"))

    def test_low_voltage_dry_three_phase_75kva(self):
        # 75 kVA LV dry-type, 35 % load: out = 0.35 x 75,000 = 26,250 W.
        # P0 250 W, Pk(75 C) 2000 W -> 250 + 0.1225 x 2000 = 495 W; eta = 26,250 / 26,745 = 98.14919 %
        e = eta(75, 0.35, 250, 2000)
        self.assertAlmostEqual(e, 98.14919, places=4)
        r = doe_efficiency_check("lv_dry", 3, 75, efficiency_pct=e, date="2020-01-01")
        self.assertEqual((r["test_load_pu"], r["required_pct"], r["status"]), (0.35, 98.60, "fail"))   # Table 2
        r = doe_efficiency_check("lv_dry", 3, 75, efficiency_pct=e, date="2012-01-01")
        self.assertEqual((r["window"]["id"], r["required_pct"], r["status"]), ("(a)(1)", 98.0, "pass"))
        # P0 150 W, Pk 1200 W -> 150 + 147 = 297 W; eta = 26,250 / 26,547 = 98.88123 % vs Table 3 (2029) 98.88
        e = eta(75, 0.35, 150, 1200)
        self.assertAlmostEqual(e, 98.88123, places=4)
        r = doe_efficiency_check("lv_dry", 3, 75, efficiency_pct=e, date="2030-01-01")
        self.assertEqual((r["window"]["id"], r["required_pct"], r["status"]), ("(a)(3)", 98.88, "pass"))

    def test_medium_voltage_dry_three_phase_1000kva_bil95(self):
        # 1000 kVA MV dry-type, BIL 95 kV -> 46-95 kV column, 50 % load: out 500,000 W.
        # P0 2000 W, Pk(75 C) 9000 W -> 2000 + 2250 = 4250 W; eta = 500,000 / 504,250 = 99.15716 %
        e = eta(1000, 0.5, 2000, 9000)
        self.assertAlmostEqual(e, 99.15716, places=4)
        r = doe_efficiency_check("mv_dry", 3, 1000, bil_kv=95, efficiency_pct=e, date="2020-01-01")
        self.assertEqual((r["bil_band"], r["required_pct"], r["status"]), ("46-95 kV", 99.20, "fail"))  # Table 9
        # P0 1500 W, Pk 7000 W -> 1500 + 1750 = 3250 W; eta = 500,000 / 503,250 = 99.35420 % >= 99.28 (Table 10)
        e = eta(1000, 0.5, 1500, 7000)
        self.assertAlmostEqual(e, 99.35420, places=4)
        r = doe_efficiency_check("mv_dry", 3, 1000, bil_kv=95, efficiency_pct=e, date="2029-04-23")
        self.assertEqual((r["window"]["id"], r["required_pct"], r["status"]), ("(c)(3)", 99.28, "pass"))
        # BIL 125 kV -> >=96 kV column, Table 9 1000 kVA 99.11 %.
        r = doe_efficiency_check("mv_dry", 3, 1000, bil_kv=125, efficiency_pct=e, date="2020-01-01")
        self.assertEqual((r["bil_band"], r["required_pct"]), (">=96 kV", 99.11))

    def test_single_phase_liquid_and_submersible(self):
        # 50 kVA single-phase liquid: P0 90 W, Pk 600 W, 50 % -> 25,000 / (25,000 + 90 + 150) = 99.04913 %
        e = eta(50, 0.5, 90, 600)
        self.assertAlmostEqual(e, 99.04913, places=4)
        r = doe_efficiency_check("liquid", 1, 50, efficiency_pct=e, date="2020-01-01")
        self.assertEqual((r["required_pct"], r["status"]), (99.11, "fail"))       # Table 5, 1-phase 50 kVA
        # Submersible from 2029-04-23 uses Table 7 (same values as Table 5), not Table 6.
        r = doe_efficiency_check("liquid", 3, 1000, efficiency_pct=99.44, date="2030-01-01", submersible=True)
        self.assertEqual((r["window"]["id"], r["required_pct"], r["status"]), ("(b)(4)", 99.43, "pass"))


class Interpolation(unittest.TestCase):
    def test_linear_between_adjacent_rows(self):
        # Table 5, 3-phase: 300 kVA 99.27, 500 kVA 99.35 -> 400 kVA: 99.27 + 0.08 x 100/200 = 99.31
        r = doe_efficiency_check("liquid", 3, 400, efficiency_pct=99.5, date="2020-01-01")
        self.assertTrue(r["interpolated"])
        self.assertAlmostEqual(r["required_pct"], 99.31, places=9)
        self.assertEqual(r["rows"], [[300.0, 99.27], [500.0, 99.35]])
        # Table 2 (LV dry), 1-phase: 50 kVA 98.30, 75 kVA 98.50 -> 60 kVA: 98.30 + 0.20 x 10/25 = 98.38
        r = doe_efficiency_check("lv_dry", 1, 60, efficiency_pct=99.0, date="2020-01-01")
        self.assertAlmostEqual(r["required_pct"], 98.38, places=9)

    def test_table6_step_interpolated_as_written(self):
        # Table 6 (2029, not submersible), 3-phase 300 kVA 99.42 and 500 kVA 99.38 (the law's values; the
        # final rule splits equipment classes at 500 kVA). 400 kVA: 99.42 - 0.04 x 0.5 = 99.40.
        r = doe_efficiency_check("liquid", 3, 400, efficiency_pct=99.41, date="2029-04-23")
        self.assertAlmostEqual(r["required_pct"], 99.40, places=9)
        self.assertEqual(r["status"], "pass")
        self.assertEqual(doe_efficiency_check("liquid", 3, 500, date="2029-04-23")["required_pct"], 99.38)

    def test_rating_not_in_table(self):
        # LV dry 3-phase tables stop at 1000 kVA: no extrapolation.
        r = doe_efficiency_check("lv_dry", 3, 1500, efficiency_pct=99.5, date="2020-01-01")
        self.assertEqual(r["status"], "not_in_table")
        self.assertIsNone(r["required_pct"])
        self.assertIsNone(r["passed"])
        self.assertEqual(r["nearest_rows"], [[1000.0, 99.28]])
        # MV dry 1-phase 15 kVA at BIL >= 96 kV: blank cell.
        r = doe_efficiency_check("mv_dry", 1, 15, bil_kv=110, efficiency_pct=99.0, date="2020-01-01")
        self.assertEqual(r["status"], "not_in_table")
        self.assertEqual(r["nearest_rows"], [[75.0, 98.53]])
        # MV dry 1-phase 60 kVA at BIL >= 96 kV: 50 kVA row blank, 75 kVA row 98.53 -> cannot interpolate.
        r = doe_efficiency_check("mv_dry", 1, 60, bil_kv=110, efficiency_pct=99.0, date="2020-01-01")
        self.assertEqual(r["status"], "not_in_table")
        # BIL below the 20 kV column.
        self.assertEqual(doe_efficiency_check("mv_dry", 3, 500, bil_kv=10, efficiency_pct=99.5,
                                              date="2020-01-01")["status"], "not_in_table")


class WindowsAndScope(unittest.TestCase):
    def test_window_boundaries(self):
        w = lambda d, k="liquid": doe_efficiency_check(k, 3, 1000, bil_kv=60, efficiency_pct=99.5, date=d)
        self.assertEqual(w("2015-12-31")["window"]["id"], "(b)(1)")
        self.assertEqual(w("2016-01-01")["window"]["id"], "(b)(2)")
        self.assertEqual(w("2029-04-22")["window"]["id"], "(b)(2)")
        self.assertEqual(w("2029-04-23")["window"]["id"], "(b)(3)")
        self.assertEqual(w("2009-12-31")["status"], "not_covered")
        self.assertEqual(w("2010-01-01", "mv_dry")["window"]["id"], "(c)(1)")
        self.assertEqual(doe_efficiency_check("lv_dry", 3, 75, efficiency_pct=99, date="2006-12-31")["status"],
                         "not_covered")
        self.assertEqual(doe_efficiency_check("lv_dry", 3, 75, efficiency_pct=99, date="2007-01-01")["window"]["id"],
                         "(a)(1)")

    def test_default_date_is_today(self):
        r = doe_efficiency_check("liquid", 3, 1000, efficiency_pct=99.5, today="2029-04-23")
        self.assertEqual((r["date"], r["window"]["id"]), ("2029-04-23", "(b)(3)"))
        r = doe_efficiency_check("liquid", 3, 1000, efficiency_pct=99.5, today="2026-10-16")
        self.assertEqual(r["window"]["id"], "(b)(2)")

    def test_by_window_lists_every_window(self):
        r = doe_efficiency_check("liquid", 3, 1000, efficiency_pct=99.5, date="2020-01-01")
        self.assertEqual([(b["id"], b["required_pct"]) for b in r["by_window"]],
                         [("(b)(1)", 99.36), ("(b)(2)", 99.43), ("(b)(3)", 99.46)])

    def test_needs_bil_and_scope(self):
        self.assertEqual(doe_efficiency_check("mv_dry", 3, 1000, efficiency_pct=99.5, date="2020-01-01")["status"],
                         "needs_input")
        for kw in ({"primary_v": 46000}, {"secondary_v": 4160}, {"frequency_hz": 50}):
            self.assertEqual(doe_efficiency_check("liquid", 3, 1000, efficiency_pct=99.5, date="2020-01-01",
                                                  **kw)["status"], "not_covered")
        self.assertEqual(doe_efficiency_check("liquid", 3, 7500, efficiency_pct=99.5, date="2020-01-01")["status"],
                         "not_covered")
        self.assertEqual(doe_efficiency_check("lv_dry", 1, 10, efficiency_pct=99.5, date="2020-01-01")["status"],
                         "not_covered")   # dry-type scope starts at 15 kVA

    def test_bad_inputs(self):
        for args, kw in ((("oil", 3, 100), {}), (("liquid", 2, 100), {}), (("liquid", 3, 0), {}),
                         (("liquid", 3, 100), {"date": "2020/01/01"})):
            with self.assertRaises(ValueError):
                doe_efficiency_check(*args, **kw)

    def test_category_from_inputs(self):
        self.assertEqual(doe_category("liquid", 480), "liquid")
        self.assertEqual(doe_category("dry", 600), "lv_dry")
        self.assertEqual(doe_category("dry", 601), "mv_dry")


class DesignIntegration(unittest.TestCase):
    def _hand(self, r):
        # eta from the design's own losses at the DOE conditions (load loss already at 55/75 C).
        d = r.doe
        return eta(r.input.kva, d["test_load_pu"], d["losses"]["no_load_w"], d["losses"]["load_loss_w"])

    def test_liquid_design_check_matches_hand_calc(self):
        r = design(TransformerInput(kva=1500, hv_v=13800, lv_v=480, doe_date="2020-01-01"))
        c = next(c for c in r.checks if c["name"] == DOE_CHECK_NAME)
        self.assertAlmostEqual(self._hand(r), r.performance["doe_point"]["efficiency_pct"], delta=0.0005)
        self.assertAlmostEqual(c["value"], self._hand(r), delta=0.0005)
        self.assertEqual(c["limit"], 99.48)          # Table 5, 3-phase 1500 kVA
        self.assertEqual(c["passed"], self._hand(r) >= 99.48)

    def test_lv_dry_design_uses_35pct(self):
        r = design(TransformerInput(kind="dry", kva=75, hv_v=480, lv_v=208, doe_date="2020-01-01"))
        self.assertEqual((r.doe["category"], r.doe["test_load_pu"], r.doe["required_pct"]), ("lv_dry", 0.35, 98.60))
        self.assertAlmostEqual(self._hand(r), r.doe["efficiency_pct"], places=9)

    def test_mv_dry_design_needs_bil(self):
        r = design(TransformerInput(kind="dry", kva=1500, hv_v=13800, lv_v=480, doe_date="2020-01-01"))
        c = next(c for c in r.checks if c["name"] == DOE_CHECK_NAME)
        self.assertFalse(c["passed"])
        self.assertIsNone(c["limit"])
        r = design(TransformerInput(kind="dry", kva=1500, hv_v=13800, lv_v=480, bil_kv=95, doe_date="2020-01-01"))
        self.assertEqual(r.doe["required_pct"], 99.30)   # Table 9, 3-phase 1500 kVA, 46-95 kV

    def test_out_of_scope_adds_no_check(self):
        r = design(TransformerInput(kva=7500, hv_v=34500, lv_v=4160, doe_date="2020-01-01"))
        self.assertEqual(r.doe["status"], "not_covered")
        self.assertFalse(any(c["name"] == DOE_CHECK_NAME for c in r.checks))


class Data(unittest.TestCase):
    def test_meta_and_monotonic_kva(self):
        self.assertEqual(DOE_DATA["_meta"]["status"], "VERIFIED")
        self.assertEqual(DOE_DATA["_meta"]["ecfr_snapshot_date"], "2026-10-14")
        for cat in DOE_DATA["categories"].values():
            for w in cat["windows"]:
                self.assertEqual(w["status"], "VERIFIED")
                for side in ("single_phase", "three_phase"):
                    k = [r[0] for r in w[side]]
                    self.assertEqual(k, sorted(set(k)), f"{w['paragraph']} {side}")

    def test_table7_equals_table5_and_table6_oddity_recorded(self):
        win = {w["id"]: w for w in DOE_DATA["categories"]["liquid"]["windows"]}
        self.assertEqual(win["(b)(4)"]["three_phase"], win["(b)(2)"]["three_phase"])
        self.assertEqual(win["(b)(4)"]["single_phase"], win["(b)(2)"]["single_phase"])
        t6 = dict(map(tuple, win["(b)(3)"]["three_phase"]))
        self.assertEqual((t6[300.0], t6[500.0]), (99.42, 99.38))
        self.assertIn("99.38", DOE_DATA["_meta"]["note"])

    def test_test_procedure_values(self):
        tp = DOE_DATA["test_procedure"]
        self.assertEqual(tp["per_unit_load"], {"liquid": 0.5, "mv_dry": 0.5, "lv_dry": 0.35})
        self.assertEqual(tp["reference_temp_c"]["liquid"], {"no_load": 20, "load": 55})
        self.assertEqual(tp["reference_temp_c"]["lv_dry"], {"no_load": 20, "load": 75})


if __name__ == "__main__":
    unittest.main()
