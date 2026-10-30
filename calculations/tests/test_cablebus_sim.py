"""Tests for the cable bus short-circuit and temperature-rise simulation (pecalc.cablebus_sim).

Each test states its reference arithmetic. Test-report ratings are user inputs, so the ratings used here are
arbitrary numbers chosen to exercise the checks, not CSA C22.2 No. 273 / IEEE C37.23 values.
"""

import math
import unittest

from pecalc import conductors as cond
from pecalc.cablebus import CableBusInput
from pecalc.cablebus_sim import (SimInput, build_context, enclosure_surface_temperature, equivalent_short_time_ka,
                                 fault_force_waveforms, first_peak_current, heat_capacity_j_per_m_k,
                                 i2t_closed_form, i2t_ka2s, sim_construction, simulate, simulate_short_circuit,
                                 simulate_temperature_rise, steady_state_cable, worst_closing_angle)
from pecalc.forces import fault_forces, peak_factor
from pecalc.thermal import CableConstruction, free_air_ampacity

# CSA 273 Figure 3 arrangement 4-1. Pinned because the best Figure 3 arrangement (4-2) shares current equally
# and is mirror symmetric, which leaves no single worst cable for these tests.
BUS = dict(voltage_v=600.0, current_a=3000.0, conductors_per_phase=4, size="750", fault_ka=50.0,
           fault_clearing_s=0.5, x_over_r=15.0, enclosure_width_mm=800.0, enclosure_height_mm=120.0,
           pattern="ABCABC/CABCAB")


class AdiabaticTemperature(unittest.TestCase):
    def test_750_cu_50ka_half_second_from_90c(self):
        # (I/A)^2 t / K = (50000/750000)^2 * 0.5 / 0.0297 = 0.0022222 / 0.0297 = 0.074823
        # T2 = (90 + 234) * 10^0.074823 - 234 = 324 * 1.18803 - 234 = 150.9 C
        t = cond.adiabatic_temperature_c("Cu", 750000, 90.0, 50000.0 ** 2 * 0.5)
        self.assertAlmostEqual(t, 150.9, delta=0.05)

    def test_inverse_of_withstand(self):
        # The withstand current for 90 -> 250 C over 0.5 s must heat the conductor to exactly 250 C.
        i = cond.adiabatic_withstand_a("Al", 500000, 90.0, 250.0, 0.5)
        self.assertAlmostEqual(cond.adiabatic_temperature_c("Al", 500000, 90.0, i * i * 0.5), 250.0, places=9)


class ShortTimeEquivalence(unittest.TestCase):
    def test_63ka_2s_equals_89ka_1s(self):
        # 63^2 * 2 = 7938 kA2s; 89^2 * 1 = 7921 kA2s (ratio 1.002); sqrt(7938 / 1) = 89.10 kA
        self.assertEqual(i2t_ka2s(63, 2), 7938)
        self.assertAlmostEqual(equivalent_short_time_ka(63, 2, 1), 89.0955, places=3)
        self.assertAlmostEqual(i2t_ka2s(89, 1) / i2t_ka2s(63, 2), 1.0, delta=0.003)

    def test_round_trip_and_errors(self):
        self.assertAlmostEqual(equivalent_short_time_ka(equivalent_short_time_ka(40, 3, 0.5), 0.5, 3), 40.0)
        with self.assertRaises(ValueError):
            equivalent_short_time_ka(40, 0, 1)


class Waveforms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = build_context(CableBusInput(**BUS))

    def test_force_peak_equals_fault_forces_exactly(self):
        c = self.ctx
        inp = c["inp"]
        fr = fault_forces(c["cs"], c["share"], inp.fault_ka, inp.x_over_r, inp.frequency_hz)
        wf = fault_force_waveforms(c["cs"], c["share"], inp.fault_ka, inp.x_over_r, inp.frequency_hz)
        self.assertEqual(wf["peak_first_cycle_n_per_m"], fr.worst_n_per_m)
        self.assertEqual(wf["worst_index"], fr.worst_index)
        self.assertEqual(wf["peak_per_conductor_n_per_m"][fr.worst_index], max(wf["force_n_per_m"][fr.worst_index]))

    def test_worst_angle_is_on_fault_forces_grid(self):
        c = self.ctx
        inp = c["inp"]
        idx, alpha = worst_closing_angle(c["cs"], c["share"], inp.fault_ka, inp.x_over_r, inp.frequency_hz)
        self.assertAlmostEqual(alpha, math.pi * idx / 24)
        # Any other grid angle gives a first-cycle peak no larger than the worst one.
        fr = fault_forces(c["cs"], c["share"], inp.fault_ka, inp.x_over_r, inp.frequency_hz)
        for other in (0, 6, 12, 18):
            wf = fault_force_waveforms(c["cs"], c["share"], inp.fault_ka, inp.x_over_r, inp.frequency_hz,
                                       closing_angle_rad=math.pi * other / 24)
            self.assertLessEqual(wf["peak_first_cycle_n_per_m"], fr.worst_n_per_m + 1e-9)

    def test_phase_currents_sum_to_zero_and_start_at_zero(self):
        c = self.ctx
        inp = c["inp"]
        wf = fault_force_waveforms(c["cs"], c["share"], inp.fault_ka, inp.x_over_r, inp.frequency_hz)
        for k in range(len(wf["t_s"])):
            self.assertAlmostEqual(sum(wf["phase_current_a"][p][k] for p in "ABC"), 0.0, places=6)
        for p in "ABC":
            self.assertAlmostEqual(wf["phase_current_a"][p][0], 0.0, places=9)

    def test_peak_factor_close_to_iec_60909(self):
        # k = sqrt(2) (1.02 + 0.98 e^(-3/15)) = 1.4142 * 1.8224 = 2.577 vs time-domain sweep
        pk = first_peak_current(50.0, 15.0)
        self.assertAlmostEqual(pk["peak_a"] / 50000 / peak_factor(15.0), 1.0, delta=0.01)

    def test_zero_dc_offset_peak(self):
        # Very low X/R: the DC term decays at once, peak -> sqrt(2) I = 70.7 kA for 50 kA.
        self.assertAlmostEqual(first_peak_current(50.0, 0.05)["peak_a"] / 1000, 70.71, delta=0.5)


class ClosedFormI2t(unittest.TestCase):
    def test_no_dc_whole_cycles_is_I2t(self):
        # th = 0: integral = amp^2 (t/2 - sin(2 w t)/(4w)) -> amp^2 t / 2 = I^2 t at whole cycles.
        amp = math.sqrt(2) * 50000
        self.assertAlmostEqual(i2t_closed_form(amp, 0.0, 0.5, 60.0, 15.0), 50000.0 ** 2 * 0.5, delta=1e-3)

    def test_matches_numeric_integration(self):
        amp, th, xr, f = 30000.0, 0.7, 12.0, 60.0
        w = 2 * math.pi * f
        n, t_end = 200000, 0.1
        dt = t_end / n
        s = 0.0
        for k in range(n):
            t = (k + 0.5) * dt
            s += (amp * (math.sin(w * t + th) - math.sin(th) * math.exp(-t * w / xr))) ** 2 * dt
        self.assertAlmostEqual(i2t_closed_form(amp, th, t_end, f, xr) / s, 1.0, places=6)


class ShortCircuitSim(unittest.TestCase):
    def test_checks_not_set_without_ratings(self):
        r = simulate_short_circuit(SimInput(bus=CableBusInput(**BUS)))
        mom = r["checks"][0]
        self.assertIsNone(mom["passed"])
        self.assertEqual(mom["status"], "NOT SET")
        self.assertFalse(r["complete"])
        self.assertEqual(r["peak_force_n_per_m"], r["worst_force_n_per_m"])  # default angle is the worst

    def test_ratings_pass_and_fail(self):
        ok = simulate_short_circuit(SimInput(bus=CableBusInput(**BUS), tested_momentary_peak_ka=140,
                                             tested_short_time_ka=63, tested_short_time_s=2))
        # 63 kA / 2 s -> sqrt(63^2 * 2 / 0.5) = 126 kA at 0.5 s, above 50 kA
        self.assertAlmostEqual(ok["equivalent_rating_ka"], 126.0, places=6)
        self.assertEqual([c["status"] for c in ok["checks"][:2]], ["PASS", "PASS"])
        bad = simulate_short_circuit(SimInput(bus=CableBusInput(**BUS), tested_momentary_peak_ka=100,
                                              tested_short_time_ka=20, tested_short_time_s=1))
        self.assertEqual([c["status"] for c in bad["checks"][:2]], ["FAIL", "FAIL"])
        self.assertIs(bad["passed"], False)

    def test_block_load_is_force_times_span(self):
        r = simulate_short_circuit(SimInput(bus=CableBusInput(**BUS)))
        self.assertAlmostEqual(r["peak_block_load_n"], r["peak_force_n_per_m"] * 0.9144, places=6)

    def test_temperature_matches_adiabatic_for_symmetrical_case(self):
        # Single conductor per phase, tiny X/R, 0.5 s: i2t of the worst conductor ~ I^2 t, so the temperature is
        # the ICEA relation with I = 50 kA (share 1): 150.9 C for 750 kcmil Cu from 90 C.
        bus = CableBusInput(voltage_v=600.0, current_a=700.0, conductors_per_phase=1, size="750", fault_ka=50.0,
                            fault_clearing_s=0.5, x_over_r=0.05, pattern="ABC")
        r = simulate_short_circuit(SimInput(bus=bus, closing_angle_deg=0.0))
        self.assertAlmostEqual(r["thermal"]["final_c"], 150.9, delta=0.5)
        self.assertGreaterEqual(r["thermal"]["final_c_worst_angle"], r["thermal"]["final_c"] - 1e-9)

    def test_errors(self):
        with self.assertRaises(ValueError):
            simulate_short_circuit(SimInput(bus=CableBusInput(**{**BUS, "fault_ka": None})))
        with self.assertRaises(ValueError):
            simulate_short_circuit(SimInput(bus=CableBusInput(**BUS), tested_short_time_ka=-1))


class SteadyState(unittest.TestCase):
    def test_at_ampacity_returns_rated_temperature(self):
        for kw in (dict(insulation_mm=2.03, insulation="XHHW", voltage_v=600.0),
                   dict(insulation_mm=7.2, insulation="EPR", shield_mm=0.13, jacket_mm=2.0, voltage_v=15000.0)):
            c = CableConstruction("750", "Cu", max_temp_c=90.0, **kw)
            for lam in (0.0, 0.2):
                a = free_air_ampacity(c, 40.0, "isolated", lam, 60.0, 90.0)
                ss = steady_state_cable(c, a.ampacity_a, 40.0, "isolated", lam, 60.0, 90.0)
                self.assertAlmostEqual(ss["theta_c"], 90.0, places=6, msg=str(kw))
                self.assertAlmostEqual(ss["surface_c"] - 40.0, a.surface_rise_c, places=6)

    def test_monotone_in_current(self):
        c = CableConstruction("500", "Cu", insulation_mm=2.03, insulation="XHHW")
        ts = [steady_state_cable(c, i, 40.0)["theta_c"] for i in (0, 100, 200, 400)]
        self.assertEqual(ts, sorted(ts))
        self.assertGreater(ts[0], 40.0 - 1e-9)

    def test_heat_balance_sums(self):
        # Ws = I^2 R (1 + l1) + Wd must equal the sum of its parts.
        c = CableConstruction("500", "Cu", insulation_mm=2.03, insulation="XHHW")
        ss = steady_state_cable(c, 300.0, 40.0, "isolated", 0.1)
        self.assertAlmostEqual(ss["heat_w_per_m"], 300.0 ** 2 * ss["r_ohm_per_m"] * 1.1 + ss["dielectric_w_per_m"])


class Enclosure(unittest.TestCase):
    def test_balance_residual_and_radiation_arithmetic(self):
        e = enclosure_surface_temperature(400.0, 800.0, 120.0, 40.0, 0.9)
        self.assertAlmostEqual(e["q_convection_w_per_m"] + e["q_radiation_w_per_m"], 400.0, places=6)
        # Radiation by hand: eps sigma (Ts^4 - Ta^4) x perimeter, perimeter = 2 (0.8 + 0.12) = 1.84 m
        ts, ta = 313.15 + e["rise_k"], 313.15
        self.assertAlmostEqual(0.9 * 5.670374419e-8 * (ts ** 4 - ta ** 4) * 1.84, e["q_radiation_w_per_m"], places=6)

    def test_more_heat_hotter_lower_emissivity_hotter(self):
        a = enclosure_surface_temperature(200.0, 800.0, 120.0, 40.0, 0.3)["rise_k"]
        b = enclosure_surface_temperature(400.0, 800.0, 120.0, 40.0, 0.3)["rise_k"]
        c = enclosure_surface_temperature(400.0, 800.0, 120.0, 40.0, 0.9)["rise_k"]
        self.assertLess(a, b)
        self.assertLess(c, b)

    def test_zero_heat_zero_rise(self):
        self.assertAlmostEqual(enclosure_surface_temperature(0.0, 800.0, 120.0, 40.0, 0.3)["rise_k"], 0.0, places=6)


class TemperatureSim(unittest.TestCase):
    def test_warmup_reaches_632_percent_at_one_time_constant(self):
        r = simulate_temperature_rise(SimInput(bus=CableBusInput(**BUS)))
        w = r["warmup"]
        # theta(tau) = ambient + rise (1 - e^-1): the sampled curve is 0 .. 5 tau in 100 steps, so tau is at k = 20.
        rise = [t - r["ambient_c"] for t in w["temp_c"]]
        self.assertAlmostEqual(rise[20] / w["rise_inf_k"], 1 - math.exp(-1), places=9)
        self.assertAlmostEqual(w["t_s"][20], w["tau_s"], places=9)
        self.assertAlmostEqual(1 - math.exp(-1), 0.632, places=3)
        self.assertAlmostEqual(w["tau_s"], w["capacity_j_per_m_k"]["total"] * w["r_th_k_m_per_w"])

    def test_capacity_hand_check_750_cu(self):
        # Conductor alone: area (mm2) x 1e-6 x 3.45e6 J/(m3 K).
        cons = sim_construction(CableBusInput(**BUS), cond.cable_od_mm("750"))
        caps = heat_capacity_j_per_m_k(cons)
        self.assertAlmostEqual(caps["conductor"], cond.area_mm2("750") * 1e-6 * 3.45e6, places=6)
        self.assertGreater(caps["total"], caps["conductor"])

    def test_checks_and_limits(self):
        r0 = simulate_temperature_rise(SimInput(bus=CableBusInput(**BUS)))
        self.assertEqual([c["status"] for c in r0["checks"]], ["PASS", "NOT SET", "NOT SET", "NOT SET"])
        r1 = simulate_temperature_rise(SimInput(bus=CableBusInput(**BUS), rise_limit_conductor_k=10.0,
                                                rise_limit_enclosure_k=100.0, rise_limit_termination_k=50.0,
                                                termination_rise_k=30.0))
        self.assertEqual([c["status"] for c in r1["checks"]], ["PASS", "FAIL", "PASS", "PASS"])
        self.assertIs(r1["passed"], False)

    def test_load_scale_raises_temperature_and_each_cable_own_current(self):
        a = simulate_temperature_rise(SimInput(bus=CableBusInput(**BUS), load_scale=0.5))
        b = simulate_temperature_rise(SimInput(bus=CableBusInput(**BUS), load_scale=1.0))
        self.assertLess(a["max_theta_c"], b["max_theta_c"])
        cur = [c["current_a"] for c in b["cables"]]
        self.assertGreater(max(cur), min(cur))      # unequal sharing -> different currents
        self.assertEqual(b["hottest"]["theta_c"], max(c["theta_c"] for c in b["cables"]))

    def test_no_enclosure_skips_estimate(self):
        bus = {k: v for k, v in BUS.items() if not k.startswith("enclosure")}
        r = simulate_temperature_rise(SimInput(bus=CableBusInput(**bus)))
        self.assertIsNone(r["enclosure"])

    def test_simulate_runs_both(self):
        r = simulate(SimInput(bus=CableBusInput(**BUS)))
        self.assertIsNotNone(r["short_circuit"])
        self.assertIsNotNone(r["temperature"])


if __name__ == "__main__":
    unittest.main()
