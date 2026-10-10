# Platform Architecture

An ETAP-style engineering platform for **equipment manufacturers**: switchgear, transformers and cable bus, for the US and Canadian markets. ETAP models a power *system*; this platform designs and verifies the *equipment* that goes into it. It is general-purpose: ratings, geometry and codes are inputs, never hard-coded to one product or project.

## Principles

1. **One engine, many products.** Conductor physics, impedance, thermal, fault-force and magnetic-field calculations are shared by every product module.
2. **Two ampacity methods, like ETAP.** Code tables (NEC / CEC) for quick, code-literal sizing, and calculated ampacity (Neher-McGrath / IEEE 835 / IEC 60287 thermal model) for any voltage, geometry or installation the tables do not cover, which the codes allow under engineering supervision.
3. **Traceable.** Every result carries the formula, inputs, intermediate values, and the code clause or standard it comes from.
4. **Data has a status.** Every table and library entry is `VERIFIED`, `UNVERIFIED` or `PLACEHOLDER`, with source and edition. Calculations refuse `PLACEHOLDER` data unless overridden, and reports print the status.
5. **Code-edition aware.** NEC 2023 / 2026, CEC (CSA C22.1) editions, and product standards are versioned data, so one design can be checked against several editions.
6. **Verified against independent references.** Every module ships with golden test cases: worked examples from standards and textbooks, manufacturer rating tables, and independent re-derivations.

## Layers

```
 UI / reports            CLI now; desktop or web UI and PDF calc packages later
 ─────────────────────────────────────────────────────────────────────────────
 Product modules         Cable bus · Switchgear / switchboard · Transformer · Feeder & cable schedule
 ─────────────────────────────────────────────────────────────────────────────
 Engineering engine      conductors · ampacity (tables + thermal model) · impedance matrix &
                         current sharing · voltage drop & losses · short circuit & forces ·
                         magnetic field · busbar thermal · transformer electromagnetics
 ─────────────────────────────────────────────────────────────────────────────
 Data & libraries        code tables by edition · cables (manufacturer datasheets) · lugs ·
                         busbar profiles · materials · enclosures · supports/blocks
 ─────────────────────────────────────────────────────────────────────────────
 Projects                design cases · revisions · snapshots · comparison (later)
```

## Product modules (scope)

| Module | Covers | Key standards |
|---|---|---|
| **Feeder & cable** | conductor sizing, parallel sets, voltage drop, losses, short-circuit withstand, lug selection | NEC 310 / 110.14(C), CEC Rules 4-004 / 4-006 / 8-102 / 8-104 / 12-108, ICEA P-32-382, UL 486A-B, NEMA CC 1 |
| **Cable bus** | 600 V–35 kV; conductor count and arrangement, current sharing among parallel conductors, ampacity, shield losses and bonding (MV), voltage drop, losses, fault forces and support/block spacing, enclosure sizing | NEC 370 / 315, CEC 12-2250 series, CSA C22.2 No. 273, IEEE C37.23, ICEA P-46-426, IEEE 835 |
| **Switchgear / switchboard** | bus sizing, temperature rise, short-circuit bracing, clearances/creepage, heat dissipation | ANSI C37.20.1/.2/.3, UL 891, UL 1558, CSA C22.2 No. 31 / 244, IEEE 605 |
| **Transformer** | preliminary electromagnetic design, losses, impedance, temperature rise, short-circuit withstand, efficiency compliance | IEEE C57.12.00/.01/.91/.96, CSA C22.2 No. 47, CSA C802, DOE 10 CFR 431 |
| **Magnetic field** | B-field maps around any conductor layout, exposure limits, induced heating in nearby steel | Biot-Savart; IEEE C95.6 / ICNIRP; NEC 300.20 |

Later, system-level studies (load flow, short circuit, arc flash) can be added by integrating an open-source solver such as pandapower or OpenDSS, rather than rebuilding them.

## Technology

- Engine: Python, pure functions, standard library only for now, so it runs unchanged on Windows and Linux. Numeric dependencies (numpy, etc.) can be added in a virtual environment when needed.
- Data: JSON files under `calculations/pecalc/data/`, one file per table and edition, each with `_meta` status, source and edition.
- Tests: `python3 -m unittest` from `calculations/`.
- UI: decide later (desktop app or web app calling the engine).

## Validation sources

Published manufacturer rating tables and worked calculations (cable bus makers' catalogues), standards' worked examples, textbook closed-form results, and independent re-derivations. Each test names its reference.

## Roadmap

1. **Engine core**: conductor physics ✅, code ampacity tables ✅ (NEC unverified, CEC placeholder), feeder sizing ✅, multi-conductor impedance and current sharing, fault forces.
2. **Cable bus v1**: any voltage 600 V–35 kV, using the shared engine; validated against published cable bus maker data.
3. **Calculated ampacity** ✅ (free air): IEC 60287 / Neher-McGrath thermal model for cables in air, tray, cable bus, conduit; shield losses for MV.
4. **Lugs and terminations.**
5. **Switchgear bus**, then **transformer**, then **magnetic field** modules.
6. Reports (PDF calc packages), project files and revisions, then a UI.
