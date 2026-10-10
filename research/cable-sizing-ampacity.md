# Cable and Conductor Sizing / Ampacity: NEC vs CEC (LV and MV)

Research note for a US/Canada electrical manufacturer (transformers, switchgear, cable bus).
Prepared 2026-10-10.

## 0. Read this first: research coverage and confidence

- Web search was rate-limited for several queries. Several results returned from search snippets only, and some came back with a warning that the answer was drawn from model memory. Those results are tagged `[UNVERIFIED]`.
- Facts verified against a fetched page are tagged `[VERIFIED: <URL>]`. Only the IAEI articles were fetched and read in full.
- The NFPA 70 page and the Southwire handbook URL did not return usable content (the Southwire URL returned 404; the Mike Holt index URL returned 404).
- No NEC or CEC table values are reproduced. Where sample numbers appear they are either from a fetched public article or are marked `[UNVERIFIED]` and need checking against the code text.
- Edition status (as of 2026-10-10):
  - NEC: NFPA 70 2026 is most likely the current edition. Published 2025 per general knowledge `[UNVERIFIED]`. The 2026 Table 310.16 rows were not confirmed.
  - CEC: CSA C22.1-24 (2024) is the edition the user named. Whether a 2027 edition is out is not confirmed `[UNVERIFIED]`.

## 1. NEC (NFPA 70) method

### 1.1 Ampacity tables (Article 310)

| Topic | What it covers | Status |
|---|---|---|
| Table 310.16 | Allowable ampacity, 60/75/90 C conductor insulation, copper and aluminum, in raceway or cable at 30 C ambient, up to 3 current-carrying conductors. | `[UNVERIFIED]` for values. Structure confirmed in CMP-6 ballot text that refers to the table for conductor insulation limits: `[VERIFIED: https://docinfofiles.nfpa.org/files/AboutTheCodes/70/70_A2025_NEC_P06_Log1691_BallotFinal.pdf]` (adds 14 AWG CCA, adjusts ambient note). |
| Table 310.17 | Single insulated conductors in free air. | `[UNVERIFIED]` |
| Table 310.18 | Conductors in raceway/cable in free air at 30 C, adjusted for ambient, with different insulation ratings. | `[UNVERIFIED]` |
| Table 310.19 / 310.20 | Conductors in underground / direct-buried duct, or ambient-adjusted tables. | `[UNVERIFIED]` |
| Table 310.21 | Ampacity of single conductors in an underground (direct-buried) context, per the referenced table list. | `[UNVERIFIED]` |
| Table 310.15(C)(1) | Adjustment factors for more than 3 current-carrying conductors in a raceway, cable or directly buried earth. | See 1.3. |

Informational annexes:
- Annex B contains ampacity tables traced back to IEEE 835 / Neher-McGrath (informational only, not mandatory). Source: `[VERIFIED (secondary): https://forums.mikeholt.com/threads/underground-raceway-calculations-nec.2563379/post-2704035]`. Treat as a forum claim until the Annex B text is checked.

### 1.2 Temperature correction (ambient)

- Table 310.15(B)(1) (formerly 310.15(B)(2)(a) in older editions) gives ambient correction factors for ambient temperatures above 30 C, applied to Table 310.16 values.
- Recent NEC editions shifted the ambient-correction location and numbering across cycles. Verify the table number in the 2026 text `[UNVERIFIED]`.

### 1.3 Adjustment for more than 3 current-carrying conductors

- Table 310.15(C)(1) (verify number) gives percentage factors for raceways, cables and direct-buried earth.
- Values as recalled `[UNVERIFIED]`:

| Current-carrying conductors | Factor |
|---|---|
| 4 to 6 | 80% |
| 7 to 9 | 70% |
| 10 to 20 | 50% |
| 21 to 30 | 45% |
| 31 to 40 | 40% |
| 41 and above | 35% |

- Neutral counting: a neutral carrying only unbalanced current is generally not counted. Verify exact wording in 310.15(E) (2023 edition) `[UNVERIFIED]`.
- Engineering supervision alternative: NEC 310.15(C) is described as the basis for the Neher-McGrath formula (secondary source): `[VERIFIED (secondary): https://www.ecmweb.com/cee-news-magazine-archive/article/20894638/code-guide]`.
  - Note: the user's reference to "310.14(B)" for engineering supervision is probably the wrong section. Confirm `[UNVERIFIED]`.

### 1.4 Parallel conductors

- Parallel conductor sets are permitted for sizes 1/0 AWG and larger, with equal length, same material, same insulation and same termination. Minimum size 1/0 AWG.
- Section number: the user cited 310.10(G) and 310.10(H). Current location is believed to be 310.10(H) for parallel conductors `[UNVERIFIED]`. Check the 2026 text.

### 1.5 Terminal temperature limits

- 110.14(C): terminations rated to 60, 75 or 90 C. Conductor ampacity for a 90 C conductor is still limited to the 60/75 C termination rating unless a higher rated termination is confirmed. `[UNVERIFIED]` wording and location.
- A forum discussion says Annex B tables are computed at 90 C conductor temperature, which conflicts with 75 C termination limits for some sizes. Secondary source only: `[VERIFIED (secondary): https://forums.mikeholt.com/threads/underground-raceway-calculations-nec.2563379/post-2704035]`.

### 1.6 Continuous load (125% rule)

- 210.19(A)(1) and 215.2(A)(1) require conductor ampacity of at least 125% of the continuous load, plus non-continuous load. Equipment-level rules (110.3(B), 240.4) may add constraints. `[UNVERIFIED]` section numbers for 2026.

### 1.7 Medium voltage (Article 311)

- Article 311 covers MV conductors (over 2 kV, up to 35 kV). Ampacity tables are Table 311.60(C) series and related table references. Verify exact numbering in the 2026 edition `[UNVERIFIED]`.
- MV ampacity is usually calculated per Neher-McGrath/IEEE 835 or per manufacturer data. Table values are for specific installation conditions.

### 1.8 Voltage drop (NEC)

- NEC informational notes (Chapter 2, 210.19 and 215.2 informational notes) recommend limits. They are not mandatory. `[VERIFIED: https://iaeimagazine.org/electrical-fundamentals/voltage-drop-formulas/]` (notes say "5 percent maximum is generally suggested", permitted range 1.5 to 15 percent, informational notes not mandatory).

## 2. CEC (CSA C22.1) method

### 2.1 Structure of Section 4

- Rule 4-004: ampacity of conductors. Rule 4-004(1) covers conductors in raceway/cable; (1)(c) covers four or more conductors in a raceway or cable using Table 2 (copper) or Table 4 (aluminum) with Table 5C correction factors. `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]` (article discusses the 2015 edition).
- Rule 12-2210 (cable trays) was expected to move into Section 4 as an extension of Rule 4-004 in the 2018 edition. Confirm in CSA C22.1-24 `[UNVERIFIED]`. Source: `[VERIFIED: https://iaeimagazine.org/?p=13523]` (describes the expected move, not the final text).

### 2.2 Ampacity tables

| Table | Covers | Status |
|---|---|---|
| Table 1 | Single copper conductors in free air, 60/75/90 C. | Structure `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]`. Values `[UNVERIFIED]`. |
| Table 2 | Copper conductors in raceway/cable, up to 3 current-carrying conductors, 30 C ambient. | Structure `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]`. |
| Table 3 | Aluminum single conductors in free air. | `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]` for structure. |
| Table 4 | Aluminum conductors in raceway/cable. | `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]` for structure. |

Sample values from secondary source (not from table text): a 3-conductor No. 6 AWG 75 C copper conductor is cited at 65 A in Table 2 `[VERIFIED (secondary): https://opentextbc.ca/plumbing4e/chapter/section-4/]`. Treat as an illustration; confirm in the CSA table.

### 2.3 Correction factors

| Table | Use | Source |
|---|---|---|
| Table 5A | Ambient above 30 C. Applied to ampacity. | `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]` for use. Values `[UNVERIFIED]`. |
| Table 5B | Up to 4 single conductors spaced under 25% of diameter, free air. Factor 0.8 mentioned in source. | `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]` (0.8 cited). |
| Table 5C | 4 or more conductors in raceway/cable; also cable trays under Rule 12-2210. Factors vary by count. Example factor 0.80 for 4 to 6 conductors `[VERIFIED (secondary): https://opentextbc.ca/plumbing4e/chapter/section-4/]`. Other bracket values `[UNVERIFIED]`. | |
| Table 5D | Single conductors spaced 25% to 100% of largest diameter, up to 6 conductors. Factor 0.84 cited. | `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]` |

- Rule 4-004(7) limits correction factors to power and lighting conductors in a cable or raceway; not to auxiliary gutters `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]`.
- Rule 4-004(3): a neutral carrying only unbalanced current is not counted. Rule 4-004(4): a neutral carrying comparable current must be counted. Rule 4-004(6): a bonding conductor is excluded `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]`.
- Table 5C factor for free-air neutral derating still applies per the article, even when the neutral is not counted under 4-004(3) `[VERIFIED (secondary): https://iaeimagazine.org/?p=13523]`.

### 2.4 Underground / direct buried

- CEC Appendix D tables (D8 to D17 per the user list) cover underground/direct-buried ampacity. Coverage not verified `[UNVERIFIED]`.

### 2.5 Terminal temperature (Rule 4-006)

- Rule 4-006 governs termination temperature limits. Equivalent of NEC 110.14(C). `[UNVERIFIED]` for current edition wording.

### 2.6 Voltage drop (Rule 8-102)

- Limits per user brief: 3% per feeder/branch circuit, 5% total from service supply point to outlet. Secondary source quoting code text (edition not stated) `[VERIFIED (secondary): https://forums.mikeholt.com/threads/3-and-5-voltage-drop.68419/post-1135392]`.
- A 2021-edition discussion says voltage drop for feeders is based on calculated demand load where overcurrent devices are chosen under other sections `[VERIFIED (secondary, forum): https://forums.mikeholt.com/threads/3-and-5-voltage-drop.68419/post-1135392]`. Confirm in 2024 text.

### 2.7 Parallel conductors (Rule 12-108 per user)

- Parallel conductor rules (user cites Rule 12-108) `[UNVERIFIED]` section number. Expected content mirrors NEC 310.10(H): min 1/0 AWG, equal length, same material and size.

### 2.8 Continuous loading (Rule 8-104)

Secondary source, 2006 article (edition not named) `[VERIFIED (secondary): https://iaeimagazine.org/2006/may2006/continuous-circuit-loading-rule-8-104/]`:

| Equipment rating | Conductor source | Max continuous loading |
|---|---|---|
| Marked 100% | Table 2 or 4, up to 3 current-carrying conductors | 100% |
| Marked 100% | Single conductors in free air, Table 1 or 3 | 85% |
| Marked 80% or unmarked | Table 2 or 4 | 80% |
| Marked 80% or unmarked | Table 1 or 3 | 70% |

- Conductor sizes from Table 1 or 3 cannot be reduced to match lower loading `[VERIFIED (secondary): same URL]`.
- The user brief said 80% / 100%. The table above is the current structure per the 2006 article. Check current Rule 8-104 text `[UNVERIFIED]`.

## 3. Voltage drop and resistance

### 3.1 Formulas

Single-phase (per IAEI, simplified DC-resistance form):
`VD = 2 x L x K x I / CM` (volts)

Three-phase:
`VD = 1.732 x L x K x I / CM` (volts)

- L = one-way length (ft), I = current (A), CM = circular mils, K = resistance per 1000 ft at 75 C (copper K = 12.9, aluminum K = 21.2, as stated in the article).
- Size form: `CM = 2 x L x K x I / %VD` (single-phase); `CM = 1.732 x L x K x I / %VD` (three-phase) `[VERIFIED: https://iaeimagazine.org/electrical-fundamentals/voltage-drop-formulas/]`.
- Uses NEC Chapter 9 Table 8 DC resistance. Reactance is not included in this form `[VERIFIED: same URL]`.

Full R and X form (IEEE 141 style), from a search snippet (garbled, verify):
`VD = K x I x (R cos phi + X sin phi)` with K = 2 (single-phase) or sqrt(3) (three-phase) `[UNVERIFIED: https://standards.globalspec.com/std/13066955/icea-p-32-382 search result, garbled]`.

- R and X source: NEC Chapter 9 Table 9 (AC resistance and reactance, 600 V, 60 Hz, conduit) `[UNVERIFIED]`.
- CEC equivalent: Appendix D, Table D3 (impedance/reactance of conductors) `[UNVERIFIED]`.

### 3.2 Conductor resistance at temperature

Standard form for copper (`[UNVERIFIED]`, widely used):
`R2 = R1 x (234.5 + T2) / (234.5 + T1)`
- Aluminum: use 228.1 instead of 234.5 `[UNVERIFIED]`.

### 3.3 I^2 R loss

`P_loss = I^2 x R_per_conductor x N_conductors` (W), with R at operating temperature. For three-phase, N = 3 `[UNVERIFIED, standard]`.

## 4. Neher-McGrath / IEEE 835 / IEEE 399

- Neher-McGrath (1957 paper): basis of NEC 310.15(C) engineering supervision method (secondary: Code Guide column). `[VERIFIED (secondary): https://www.ecmweb.com/cee-news-magazine-archive/article/20894638/code-guide]`
- IEEE 835 (Standard Power Cable Ampacity Tables): tabulates extruded dielectric cable ampacities up to 138 kV and laminar dielectric cables up to 500 kV, over 3000 tables. `[VERIFIED (search snippet, secondary): https://standards.globalspec.com/std/751264/ieee-835]`. Treat the exact table count as `[UNVERIFIED]`.
- IEEE 399 is commonly cited for power-system analysis (the Brown Book), not for cable ampacity `[UNVERIFIED]`. The user should confirm which IEEE standard they meant. IEEE 835 is the ampacity standard.
- Practical note from secondary sources: hand Neher-McGrath calculations are accepted under engineering supervision, but commercial verified software is the industry norm `[VERIFIED (secondary): https://forums.mikeholt.com/threads/underground-raceway-calculations-nec.2563379/post-2704035]`.

## 5. Short-circuit withstand of conductors

- ICEA P-32-382 covers short-circuit calculations for copper and aluminum conductors. Adiabatic assumption (heat stays in conductor). Covering/insulation temperature limits per material `[VERIFIED (search summary): https://standards.globalspec.com/std/13066955/icea-p-32-382]`.
- Edition status unclear: one listing shows 2007, another shows a 2007 reaffirmed in 2018, another shows a 2025 edition `[VERIFIED (listing): same URL]`. Confirm current edition.
- Thermoplastic short-circuit limit cited as 150 C in an older edition (secondary forum) `[UNVERIFIED]`. Mike Holt material cites damage temperature for 75 C thermoplastic as 150 C `[VERIFIED (secondary): https://www.mikeholt.com/documents/EE/word/conductorshort-circuitprotection.doc]`.
- Adiabatic relation (widely used in ICEA/IEEE derivations) `[UNVERIFIED, from memory]`:
  - `I^2 * t = 0.0297 * A^2 * log10((T2 + 234) / (T1 + 234))` for copper, A in circular mils, t in seconds.
  - Aluminum constant is about 0.0125 `[UNVERIFIED]`.
  - Equivalent in A/mm2 form exists in IEC 60949 (comparison only).
- Conductor shield: search found no shield-specific limits. ICEA P-45-482 covers metallic shields `[VERIFIED (listing): https://standards.globalspec.com/std/14611578/p-45-482]`.

## 6. Algorithm for implementation

Inputs:
- code: NEC or CEC
- conductor material (Cu/Al), insulation rating (60/75/90 C)
- installation: raceway/cable, free air, direct buried, cable tray
- number of current-carrying conductors (for adjustment), ambient temperature, burial/spacing
- load current (continuous flag), equipment marking (80%/100%), termination rating
- length (one-way), phases, voltage, power factor, voltage drop limit (% or code-based)
- MV flag (Article 311 or equivalent CEC), short-circuit current and duration (if withstand check)

Steps:
1. Determine design current: `I_design = I_load * 1.25` if continuous (NEC 210.19/215.2; CEC 8-104 context). Apply equipment derating: `I_design <= 0.8 * equipment rating` (80% equipment) or per Rule 8-104 table above (CEC).
2. Choose base ampacity table from installation type (NEC 310.16/17/18/19/20/21, or CEC Table 1/2/3/4, D-tables for underground).
3. Apply ambient correction (NEC 310.15(B)(1) / CEC Table 5A).
4. Apply conductor-count adjustment (NEC 310.15(C)(1) / CEC Table 5C). Do not count neutral with only unbalanced current (NEC 310.15(E) / CEC 4-004(3)).
5. Apply termination limit: `I_allow = min(ampacity_adjusted, termination_rating_ampacity)` (NEC 110.14(C) / CEC 4-006).
6. Select smallest conductor size with `I_allow >= I_design`. If none, go to parallel sets (NEC 310.10(H) / CEC 12-108): `N_parallel = ceil(I_design / ampacity_one_set)`, min 1/0 AWG per set, identical lengths and material.
7. Voltage drop check:
   - `VD_pct = K * L * I * (R cos phi + X sin phi) / (V_LL_or_LN) * 100` with K = 2 (1-phi) or sqrt(3) (3-phi). Use R at operating temperature (Section 3.2). Use X from NEC Ch.9 Table 9 / CEC D3.
   - Compare to 3% per circuit and 5% total (CEC 8-102) or 5% suggested (NEC informational note).
   - If fails, increase size or parallel sets and repeat.
8. Losses: `P_loss = N_phase * I^2 * R_op * L` (W per phase set).
9. Short-circuit withstand (optional): `I_sc_min_ok` from adiabatic relation (Section 5). Verify conductor and shield temperature limits.
10. Output: selected conductor size per phase, number of parallel sets, ampacity used (after all derates), %VD, losses per run, limiting factor, code references.

Edge cases to handle in code:
- Cable tray (NEC 392, CEC 12-2210) spacing and tray-fill rules are separate.
- MV (NEC 311, CEC 4-section MV) uses Neher-McGrath or IEEE 835 data, not the LV table path.
- Multiple conductor configurations in duct banks need thermal-resistance calc, not the table path.

## 7. NEC vs CEC differences (summary)

| Topic | NEC (NFPA 70) | CEC (CSA C22.1) |
|---|---|---|
| Ampacity tables | Table 310.16 (raceway/cable), 310.17 (free air), 310.18 onward | Tables 1 to 4 (free air vs raceway), Appendix D for underground |
| Conductor-count adjustment | 310.15(C)(1) percentages (80/70/50/45/40/35%) `[UNVERIFIED values]` | Table 5C; factors differ by count `[UNVERIFIED values]` |
| Free-air spacing | Table 310.17 | Tables 1/3 with 5B (spacing under 25%, up to 4 conductors) or 5D (25% to 100%, up to 6) |
| Ambient correction | Table 310.15(B)(1) (verify) | Table 5A |
| Neutral counting | 310.15(E) (verify) | Rule 4-004(3), (4) |
| Voltage drop | Informational note, 5% suggested, not mandatory | Rule 8-102: 3% per circuit, 5% overall, mandatory `[VERIFIED (secondary)]` |
| Continuous load | 125% (210.19, 215.2) | Rule 8-104 table: 100/85/80/70% depending on equipment marking and conductor table (2006 article) `[VERIFIED (secondary)]` |
| Parallel conductors | 310.10(H), min 1/0 `[UNVERIFIED section]` | Rule 12-108 `[UNVERIFIED]` |
| Termination | 110.14(C) | Rule 4-006 `[UNVERIFIED]` |
| Engineering supervision | 310.15(C) per secondary source `[VERIFIED (secondary)]`, user cited 310.14(B) (check) | Rule 4-004(1)(d) (user's cite, not verified) |
| Cable trays | NEC Article 392 | Rule 12-2210 (moving into Section 4 per 2015 article) |

## 8. Sources

Verified (fetched):
- https://iaeimagazine.org/electrical-fundamentals/voltage-drop-formulas/ (voltage drop formulas, K values, NEC informational notes)
- https://iaeimagazine.org/2006/may2006/continuous-circuit-loading-rule-8-104/ (CEC Rule 8-104 continuous loading, 2006 article)
- https://iaeimagazine.org/?p=13523 (CEC Rules 4-004 and 12-2210, 2015 edition; tables 1 to 5D use and neutral counting)

Verified (search snippet or listing, secondary):
- https://iaeimagazine.org/2015/september-october2015/rules-4-004-and-12-2210-intricacies-of-application/
- https://opentextbc.ca/plumbing4e/chapter/section-4/ (Table 5C example, worked No. 6 AWG)
- https://forums.mikeholt.com/threads/underground-raceway-calculations-nec.2563379/post-2704035 (Annex B, IEEE 835 link, 90 C vs 75 C discussion)
- https://www.ecmweb.com/cee-news-magazine-archive/article/20894638/code-guide (Dann Strube column; 310.15(C) and Neher-McGrath)
- https://forums.mikeholt.com/threads/3-and-5-voltage-drop.68419/post-1135392 (CEC Rule 8-102 quoted text, edition unknown)
- https://docinfofiles.nfpa.org/files/AboutTheCodes/70/70_A2025_NEC_P06_Log1691_BallotFinal.pdf (CMP-6 ballot text on Table 310.16)
- https://docinfofiles.nfpa.org/files/AboutTheCodes/70/70_A2025_NEC_P06_FD_PrelimFR.pdf (proposed 2026 changes, Table 310.4(1))
- https://iaeimagazine.org/columns/nfpa-code-talk/look-at-proposed-2026-nec-changes/ (proposed 2026 changes overview)
- https://standards.globalspec.com/std/13066955/icea-p-32-382 (ICEA P-32-382 listing and scope)
- https://standards.globalspec.com/std/14611578/p-45-482 (ICEA P-45-482 listing)
- https://www.mikeholt.com/documents/EE/word/conductorshort-circuitprotection.doc (short-circuit damage temperature summary)
- https://standards.globalspec.com/std/751264/ieee-835 (IEEE 835 listing)

Not usable (404 or no content):
- https://www.nfpa.org/codes-and-standards/nfpa-70-standard-development/70 (no edition info returned)
- https://www.southwire.com/handbook (404)
- https://www.mikeholt.com/mojoomla/index.php (404)

## 9. Open questions / needs checking

1. Confirm NEC 2026 edition text for Tables 310.16, 310.15(B)(1) (ambient), 310.15(C)(1) (count factors), 310.15(E) (neutral), 310.10(H) (parallel). Numbers in this file are from memory unless tagged VERIFIED.
2. Confirm NEC engineering-supervision section: 310.15(C) per secondary source vs user's 310.14(B).
3. Confirm CEC 2024 Table 5C bracket values and Table 5A values from the purchased CSA C22.1-24 text.
4. Confirm CEC Rule 8-104 current wording (2006 article is old; 80/100% vs 70/85% details).
5. Confirm CEC Rule 8-102 wording and whether 3%/5% applies to feeders and branches as the user described.
6. Confirm CEC Rule 12-108 (parallel) and Rule 4-006 (termination) numbers and text.
7. Confirm CEC Rule 4-004(1)(d) reference for engineering supervision (user cited); may not exist.
8. Confirm Appendix D tables (D3, D8 to D17) content and whether D3 is resistance/reactance.
9. Clarify IEEE 399 vs IEEE 835 reference (user's brief). IEEE 835 is the ampacity standard `[UNVERIFIED]` for IEEE 399 scope.
10. ICEA P-32-382 current edition and the exact adiabatic equation and constants. Confirm 0.0297 / 0.0125 constants against the standard.
11. Confirm Article 311 Table 311.60 numbering for MV ampacity in NEC 2026.
12. Confirm whether CSA C22.1-27 exists or is in progress as of 2026-10-10.
13. Search was rate-limited; a second pass with the official NFPA free-view site and CSA/IEEE store pages is needed for final values.
