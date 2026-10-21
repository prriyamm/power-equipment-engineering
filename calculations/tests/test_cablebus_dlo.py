"""Cable bus with the DLO cable library (cable_type 'dlo_2000v').

Hand values are worked in the comments. Printed manufacturer values come from data/dlo_cables.json
(Southwire DLO specification sheet; AWC DLO-1111 page). No datasheet DC resistance exists in the
library, so the DC resistance tests that use a printed value pass one in explicitly (test values only).
"""

import math
import unittest

from pecalc import ampacity as amp
from pecalc import cablebus as cb
from pecalc import conductors as cond


class LibraryData(unittest.TestCase):
    def test_library_rows_and_sources(self):
        entries = cb.library_entries()
        self.assertEqual(len(entries), 18)                       # 17 Southwire rows + AWC 1111
        sw = cb.cable_spec("southwire_dlo_2000v:444.4")
        self.assertEqual(sw.status, "MANUFACTURER")
        self.assertIn("houseofelectrical.com", sw.source_url)
        self.assertEqual(sw.rated_voltage_v, 2000.0)
        self.assertEqual(sw.temp_c, 90)

    def test_hand_values_444_kcmil(self):
        # Printed on the Southwire sheet: 444.4 kcmil, 1110 x 24 AWG strands, insulation 2.41 mm,
        # nominal OD 31.24 mm (1.23 in), free-air rating 652 A (NEC 310.17 basis, 90 C, 30 C ambient).
        sw = cb.cable_spec("southwire_dlo_2000v:444.4")
        self.assertEqual(sw.area_cmil, 444400)
        self.assertAlmostEqual(sw.area_cmil * cond.CMIL_TO_MM2, 225.18, places=2)   # 444 400 x 5.067e-4 mm2
        self.assertAlmostEqual(sw.od_mm, 31.24)
        self.assertAlmostEqual(sw.insulation_mm, 2.41)
        self.assertEqual(sw.ampacity_free_air_a, 652.0)
        self.assertFalse(sw.standard_nec_size)

    def test_non_standard_size_is_refused_by_the_code_size_list(self):
        # The DLO sizes stay out of the NEC size list used by the code tables.
        with self.assertRaises(ValueError):
            cond.normalize_size("444.4")

    def test_bad_cable_ids(self):
        for bad in ("southwire_dlo_2000v:9999", "nope:444.4", "southwire_dlo_2000v", ""):
            with self.assertRaises(ValueError, msg=bad):
                cb.cable_spec(bad)

    def test_1111_kcmil_basis_not_stated(self):
        awc = cb.cable_spec("awc_dlo_2000v:1111")
        self.assertFalse(awc.basis_stated)
        self.assertEqual(awc.od_mm, 45.49)                       # 1.791 in
        self.assertEqual(awc.area_cmil, 1_111_000)


class ConductorHandChecks(unittest.TestCase):
    def test_dc_resistance_calculated_at_90_c(self):
        # rho20 10.371 ohm-cmil/ft / 444 400 cmil = 2.33355e-5 ohm/ft; x 1.02 stranding = 2.38038e-5 ohm/ft.
        # Temperature to 90 C: x (234.5 + 90) / (234.5 + 20) = x 1.275049 -> 3.03510e-5 ohm/ft.
        # Per metre: / 0.3048 = 9.9577e-5 ohm/m (0.03035 ohm per 1000 ft).
        r = cond.rdc_from_area_ohm_per_m(444400, "Cu", 90.0, 1.02)
        self.assertAlmostEqual(r, 9.9577e-5, delta=1e-8)
        self.assertAlmostEqual(r * 0.3048 * 1000, 0.03035, places=5)

    def test_datasheet_dc_value_is_corrected_to_operating_temperature(self):
        # TEST VALUE ONLY (no printed DC value exists in the library): 0.030 ohm/1000 ft at 20 C.
        # To 90 C: 0.030 / 1000 / 0.3048 x (234.5 + 90) / (234.5 + 20) = 9.8425e-5 x 1.275049 = 1.25497e-4 ohm/m.
        r = cond.rdc_datasheet_ohm_per_m(0.030, 20.0, "Cu", 90.0)
        self.assertAlmostEqual(r, 1.25497e-4, delta=1e-9)

    def test_diameter_proxy_and_layout_pitch(self):
        # Conductor diameter (no printed value): sqrt(444 400) / 1000 x 1.173 = 0.66663 x 1.173 in = 19.86 mm.
        # Default centre spacing is 2 x OD = 2 x 31.24 mm = 62.48 mm.
        sw = cb.cable_spec("southwire_dlo_2000v:444.4")
        self.assertEqual(sw.diameter_source, "proxy")
        self.assertAlmostEqual(sw.diameter_mm, 19.86, places=2)
        r = cb.analyse(cb.CableBusInput(voltage_v=600.0, current_a=1500.0, conductors_per_phase=3,
                                        size="444.4", cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:444.4"))
        self.assertAlmostEqual(r.cable_od_mm, 31.24)
        self.assertAlmostEqual(r.pitch_mm, 62.48)


class AmpacityBasis(unittest.TestCase):
    def test_datasheet_ampacity_with_ambient_correction(self):
        # 444.4 kcmil, printed free-air rating 652 A at 30 C. At 40 C with 90 C conductor:
        # 652 x sqrt((90 - 40) / (90 - 30)) = 652 x 0.912871 = 595.19 A.
        r = cb.analyse(cb.CableBusInput(voltage_v=600.0, current_a=1500.0, conductors_per_phase=3,
                                        size="444.4", cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:444.4",
                                        ambient_c=40.0))
        self.assertIn("652 A at 30 C", r.ampacity_basis)
        self.assertIn("0.913", r.ampacity_basis)
        loading = next(c for c in r.checks if c["name"].startswith("Most heavily loaded conductor within its"))
        self.assertAlmostEqual(loading["limit"], 595.19, delta=0.06)   # rounded to 0.1 A in the conductor row

    def test_standard_size_uses_code_table_when_listed(self):
        # 4/0 AWG is a standard NEC size and the series is listed RHH/RHW: code table, NEC 310.17, 90 C column.
        # Table 405 A x sqrt((90 - 40) / (90 - 30)) = 369.71 A at 40 C.
        r = cb.analyse(cb.CableBusInput(voltage_v=600.0, current_a=600.0, conductors_per_phase=1, size="4/0",
                                        cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:4/0", ambient_c=40.0))
        self.assertIn("NEC Table 310.17", r.ampacity_basis)
        self.assertIn("405 A", r.ampacity_basis)
        self.assertEqual(amp.table_ampacity("NEC", "free_air", "Cu", "4/0", 90), 405.0)

    def test_table_method_refused_for_non_standard_size(self):
        with self.assertRaises(ValueError):
            cb.analyse(cb.CableBusInput(voltage_v=600.0, current_a=1500.0, size="444.4", ampacity_method="table",
                                        cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:444.4"))

    def test_calculated_method_refused_for_library_cable(self):
        with self.assertRaises(ValueError):
            cb.analyse(cb.CableBusInput(voltage_v=600.0, current_a=1500.0, size="444.4", ampacity_method="calculated",
                                        cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:444.4"))

    def test_unstated_basis_is_flagged(self):
        r = cb.analyse(cb.CableBusInput(voltage_v=600.0, current_a=1500.0, conductors_per_phase=1, size="1111",
                                        cable_type="dlo_2000v", cable_id="awc_dlo_2000v:1111"))
        self.assertTrue(any(n.startswith("WARNING: the maker does not state") for n in r.notes))
        self.assertIsNotNone(r.cable_data)
        self.assertEqual(r.cable_data["status"], "MANUFACTURER")


class Rules(unittest.TestCase):
    def dlo(self, **kw):
        base = dict(voltage_v=600.0, current_a=1000.0, conductors_per_phase=2, size="444.4",
                    cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:444.4")
        base.update(kw)
        return cb.CableBusInput(**base)

    def test_voltage_above_rating_is_refused(self):
        with self.assertRaises(ValueError) as cm:
            cb.analyse(self.dlo(voltage_v=2400.0))
        self.assertIn("rated 2000 V", str(cm.exception))
        cb.analyse(self.dlo(voltage_v=2000.0))                    # at the rating is allowed

    def test_copper_only_and_90_c_only(self):
        with self.assertRaises(ValueError):
            cb.analyse(self.dlo(material="Al"))
        with self.assertRaises(ValueError):
            cb.analyse(self.dlo(insulation_temp_c=75))

    def test_cable_type_and_cable_id_must_agree(self):
        with self.assertRaises(ValueError):
            cb.analyse(cb.CableBusInput(size="750", cable_type="dlo_2000v"))          # no cable_id
        with self.assertRaises(ValueError):
            cb.analyse(cb.CableBusInput(size="750", cable_type="standard", cable_id="southwire_dlo_2000v:444.4"))
        with self.assertRaises(ValueError):
            cb.analyse(cb.CableBusInput(size="750", cable_type="barge"))

    def test_insulation_inputs_not_used_with_library_cable(self):
        with self.assertRaises(ValueError):
            cb.analyse(self.dlo(insulation_mm=2.41))

    def test_parallel_minimum_by_area(self):
        # 8 AWG DLO (16 510 cmil) is below the 1/0 AWG (105 600 cmil) minimum for paralleled conductors.
        r = cb.analyse(cb.CableBusInput(voltage_v=600.0, current_a=200.0, conductors_per_phase=2, size="8",
                                        cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:8"))
        par = next(c for c in r.checks if c["name"].startswith("Minimum size"))
        self.assertFalse(par["passed"])
        self.assertEqual(par["limit"], 105600.0)
        r2 = cb.analyse(cb.CableBusInput(voltage_v=600.0, current_a=800.0, conductors_per_phase=2, size="4/0",
                                         cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:4/0"))
        self.assertTrue(next(c for c in r2.checks if c["name"].startswith("Minimum size"))["passed"])

    def test_termination_note_present(self):
        r = cb.analyse(self.dlo())
        self.assertTrue(any("fine-stranded" in n for n in r.notes))

    def test_standard_default_has_no_library_data(self):
        r = cb.analyse(cb.CableBusInput(voltage_v=600.0, current_a=1000.0, size="750"))
        self.assertIsNone(r.cable_data)
        self.assertEqual(r.input.cable_type, "standard")
        self.assertIsNone(r.input.cable_id)


class PrintedResistance(unittest.TestCase):
    def test_printed_dc_value_path_is_used_when_present(self):
        # Test-only spec with a printed DC value of 0.030 ohm/kft at 20 C; analysis must use it (not the calc).
        spec = cb.cable_spec("southwire_dlo_2000v:444.4")
        printed = cb.CableSpec(**{**spec.__dict__, "rdc_ref": (0.030, 20.0)})
        self.assertAlmostEqual(cb._library_rdc_ohm_per_m(printed, 90.0), 1.25497e-4, delta=1e-9)
        self.assertNotAlmostEqual(cb._library_rdc_ohm_per_m(spec, 90.0), 1.25497e-4, delta=1e-6)


class Drawing(unittest.TestCase):
    def test_title_labels_library_size_with_unit(self):
        from pecalc.drawing import cablebus_svg
        inp = cb.CableBusInput(voltage_v=600, current_a=1000, conductors_per_phase=2, size="444.4",
                               cable_type="dlo_2000v", cable_id="southwire_dlo_2000v:444.4",
                               enclosure_width_mm=400, enclosure_height_mm=150)
        self.assertIn(">2 x 444.4 kcmil Cu per phase, ", cablebus_svg(inp, cb.analyse(inp)))


if __name__ == "__main__":
    unittest.main()
