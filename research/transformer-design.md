# Transformer Design and Application Calculations: Research Notes

Scope: US and Canada distribution/power transformers (dry-type and liquid-filled), with IEC as comparison only.
Research date: 2026-10-10.

Tag key:
- **[VERIFIED: URL]**: confirmed in a page or search result retrieved during this research.
- **[UNVERIFIED]**: from general engineering knowledge or a secondary excerpt, not checked against the primary document. Treat as a lead, not a fact.

Summary of confidence: standards identity, status and scope are mostly verified. Clause-level content (equations, category tables, loss formulas, loading-guide constants) is mostly UNVERIFIED because the primary texts are paywalled and were not retrieved.

---

## 1. Applicable standards

| Standard | Covers | Status found | Tag |
|---|---|---|---|
| IEEE C57.12.00 | General requirements, liquid-immersed distribution, power, regulating transformers (ratings, tests, short-circuit categories, temp rise) | Active; 2021 edition listed | [VERIFIED: https://standards.ieee.org/standard/C57_12_00-2021.html] (title and status); scope text not retrieved |
| IEEE C57.12.01 | General requirements, dry-type distribution and power transformers (incl. cast/resin-encapsulated) | Older edition (1998) seen in IEEE listings; current edition not confirmed | [VERIFIED: https://grouper.ieee.org/groups/transformers/notices/C57-2002%20contents.pdf] (title, older edition only) |
| IEEE C57.12.90 | Test code for liquid-immersed transformers (resistance, ratio, no-load/load loss, impedance, dielectric, temp rise, short-circuit, sound). Excludes instrument, regulator, arc furnace, rectifier, grounding, mine transformers | Active; 2021 edition listed | [VERIFIED: https://standards.ieee.org/ieee/C57.12.90/4559] (scope summary via search); 2021 status via IEEE listing |
| IEEE C57.12.91 | Test code, dry-type | Not verified | [UNVERIFIED] |
| IEEE C57.12.34 | Pad-mounted, compartmental-type, three-phase distribution transformers | Not searched | [UNVERIFIED] |
| IEEE C57.12.36 | Liquid-immersed substation transformers (pad-mount/ substation scope) | Not searched | [UNVERIFIED] |
| IEEE C57.12.80 | Terminology | Not searched | [UNVERIFIED] |
| IEEE C57.91 | Liquid-immersed loading guide (aging, hot-spot, loading limits) | Current edition believed to be C57.91-2011; not verified in this session | [UNVERIFIED] (edition); see Section 4 |
| IEEE C57.96 | Dry-type loading guide | 2013 edition now **inactive** (inactivated 2024-03-21). PAR approved 2021-02-10 for replacement "PC57.96" | [VERIFIED: https://standards.ieee.org/standard/C57_96-2013.html] and [VERIFIED: https://standards.ieee.org/ieee/C57.96/10554/] |
| IEEE C57.110 | Recommended practice for capability with nonsinusoidal (harmonic) loads. Current = 2018 revision (2008 superseded) | Active | [VERIFIED: https://infostore.saiglobal.com/en-us/Standards/IEEE-C-57-110-2008-571403_SAIG_IEEE_IEEE_1307743/] (2008 redline, edition history) and search summary of 2018 edition |
| IEEE C57.109 | Guide for through-fault-current duration / protection coordination for Categories I–IV | 2018 edition active; PAR approved 2026-02-12 to supersede | [VERIFIED: https://standards.ieee.org/standard/C57_109-2018.html] and [VERIFIED: https://standards.ieee.org/ieee/C57.109/12481] |
| CSA C22.2 No. 47 | Air-cooled dry-type power/heating/lighting transformers (incl. K-factor ratings via TIL I-28). Excludes specialty units and energy performance (see C802.2) | Current: CAN/CSA C22.2 No. 47-13 (R2023); reaffirmed 2018 | [VERIFIED: https://scc-ccn.ca/standardsdb/standards/4027191] and [VERIFIED: https://webstore.ansi.org/standards/csa/csac22472013r2018] |
| CSA C22.2 No. 66 | Specialty and low-voltage transformers, ferroresonant, Class 2/3. Split into Parts 66.1 (general requirements) and 66.2 (general-purpose) | Original 1988 edition withdrawn (superseded by 66.3-06 per search). Current: 66.1-06 (R2025) and 66.2:21 (R2025) | [VERIFIED: https://ccn-scc.ca/standardsdb/standards/4003379] (1988 status) and [VERIFIED: https://www.csagroup.org/store/product/2700509] (66.1/66.2 listing per search) |
| CSA C802.2 | Efficiency test method and minimum efficiency values for **dry-type** transformers. Current CAN/CSA C802.2-18 (R2023), 15–833 kVA single-phase, 15–7500 kVA three-phase, HV ≤35 kV, 60 Hz | Current | [VERIFIED: https://webstore.ansi.org/standards/csa/csac80218r2023] and [VERIFIED: https://ccn-scc.ca/standardsdb/standards/4007539] (older 2000 edition) |
| CSA C802.1 | Efficiency for liquid-immersed (per search: not checked) | Not verified | [UNVERIFIED] |
| CSA C88 | Not searched | Not verified | [UNVERIFIED] |
| UL 1561 | General purpose and power, dry-type, 600 V class and below; air-cooled; for NEC use. Excludes liquid-filled, >600 V, and rectifier/waveshaping units | Active | [VERIFIED: https://americas.hammondpowersolutions.com/resources/faq/definition/what-is-ul-1561] and [VERIFIED: https://standards.globalspec.com/std/14541976/ul-1561] |
| UL 1562 | Distribution, dry-type, over 600 V (601–35,000 V); cast-coil and resin-encapsulated; excludes utility-owned, instrument, regulators, arc-furnace, rectifier, mining | Active | [VERIFIED: https://americas.hammondpowersolutions.com/resources/faq/definition/what-is-ul-1562] and [VERIFIED: https://standards.globalspec.com/std/14543333/ul-1562] |
| UL 506 | Specialty transformers; cross-references UL 1561/1562 | Active | [VERIFIED: https://datasheets.globalspec.com/ds/uls/ul-506/dbaaaa5f-1a2d-4c28-b5d5-c5849ccc00be] |
| NEMA TP-1 | Efficiency (historical); withdrawn by NEMA per SCC notice | Withdrawn | [VERIFIED: https://scc-ccn.ca/standards/notices-of-intent/csa-group/minimum-efficiency-values-dry-type-transformers-0] (via search summary) |

### 1.1 US DOE efficiency (10 CFR 431, Subpart K)

- **2016 rule:** Original DOE distribution transformer standards (NEMA TP-1 / 2016 levels). [UNVERIFIED for specific levels; not retrieved in this session.]
- **2024 final rule (current):** Published April 22, 2024, 89 FR 29834, docket EERE-2019-BT-STD-0018. Effective July 8, 2024. **Compliance date April 23, 2029.**
  - [VERIFIED: https://www.govinfo.gov/content/pkg/FR-2024-04-22/html/2024-07480.htm]
  - Adopted TSL 3. Per the rule text (as extracted): for liquid-immersed units, loss reductions of 5% (single-phase ≤100 kVA and three-phase ≥500 kVA) and 20% (single-phase >100 kVA and three-phase <500 kVA), relative to the baseline. For low-voltage dry-type, reductions of 30% (single-phase) and 20% (three-phase). [VERIFIED: same URL]
  - Coverage: liquid-immersed 10–2,500 kVA; low-voltage dry-type 15–2,500 kVA. [VERIFIED: same URL]
  - Test procedure: 10 CFR 431 Subpart K, Appendix A. [VERIFIED: same URL]
  - Efficiency values and per-kVA loss formulas are in Tables I.1–I.3 of the rule; **not retrieved** (the extracted text omitted them). [UNVERIFIED: need the tables]
  - Medium-voltage dry-type is covered by the same rule. [UNVERIFIED for levels]
- **"2027" date:** The 2027 date belonged to the December 2022 *proposed* rule (which would have pushed amorphous-core designs). It was superseded by the 2024 final rule. [VERIFIED: https://www.powermag.com/doe-proposes-new-distribution-transformer-standards-as-crippling-shortages-persist] (search summary)
- **2026 status:** A Presidential determination (April 20, 2026) on grid supply chains led DOE to issue an RFI (docket EERE-2026-BT-STD-0133) on the 2024 standards. Comments were due July 15, 2026. No new final rule found. [VERIFIED: https://public-inspection.federalregister.gov/2026-11971.pdf] (search result; content not read in full). **Check Federal Register for changes before any compliance decision.**

### 1.2 Canadian efficiency

- CSA C802.2-18 (R2023) is the dry-type efficiency standard. It recommends the total ownership cost (TOC) method. Harmonization with DOE values and inclusion of NEMA TP-1 is an open project per an SCC notice; no newer edition found. [VERIFIED: https://webstore.ansi.org/standards/csa/csac80218r2023] and [VERIFIED: https://scc-ccn.ca/standards/notices-of-intent/csa-group/minimum-efficiency-values-dry-type-transformers-0]
- Table 1 minimum efficiency values **not retrieved**. [UNVERIFIED]
- Liquid-filled efficiency in Canada: not established in this session. [UNVERIFIED]

### 1.3 Short-circuit, through-fault, and protection

- **C57.12.00 categories I–IV:** Categories depend on kVA and phase, and set through-fault withstand. The category table itself was **not retrieved**. Recollection (UNVERIFIED, do not use for design):
  - Cat I: ~5–500 kVA single-phase, 15–500 kVA three-phase
  - Cat II: ~501–1,667 kVA single-phase, 501–5,000 kVA three-phase
  - Cat III: ~1,668–10,000 kVA single-phase, 5,001–30,000 kVA three-phase
  - Cat IV: above those
  - Duration: commonly cited as 2 s for the mechanical/thermal withstand test. [UNVERIFIED]
- **C57.109:** Provides coordination curves (fault magnitude vs duration) for the four categories, and is used to set relay/fuse curves. Scope [VERIFIED: https://online.standard.no/en/ieee-c57109]; 2018 edition and PAR 2026 as in Section 1 table.
- **IEC 60076-5** (comparison only): Categories by power, 25–2,500 kVA (Cat I), 2,501–100,000 kVA (Cat II), >100,000 kVA (Cat III). These boundaries differ from IEEE and must not be mixed. [VERIFIED: search result summary, source not checked]

### 1.4 Harmonics

- C57.110-2018 applies to general-purpose transformers where load-current THD is above roughly 5% (per secondary summary). [VERIFIED: https://powerquality.blog/2024/09/13/an-introduction-to-transformer-harmonic-current-derating-metrics/] (secondary)
- The K-factor (UL 1561/1562) and C57.110 harmonic loss factor (F_HL) are **not interchangeable**. C57.110 has an informative annex comparing them. [VERIFIED: https://infostore.saiglobal.com/...C-57-110-2008 redline] (summary)
- CSA C22.2 No. 47 incorporated K-factor ratings (TIL I-28). [VERIFIED: https://webstore.ansi.org/standards/csa/csac22472013r2018]

---

## 2. Core design equations

Most equations below are standard textbook forms. None were verified against Kulkarni & Khaparde in this session (the book's text was not found). Treat every equation as **[UNVERIFIED]** until checked.

### 2.1 EMF equation

E_rms = 4.44 · f · N · B_m · A_c

- f = frequency (Hz), N = turns, B_m = peak flux density (T), A_c = net core area (m²). [UNVERIFIED]
- Volts per turn: V_t = 4.44 · f · B_m · A_c. [UNVERIFIED]
- Turns per volt: N/V = 1 / (4.44 · f · B_m · A_c). [UNVERIFIED]

### 2.2 Output equation (core area × window area)

Single-phase: S = 2.22 · f · B_m · A_i · A_w · K_w · δ · 10⁻³ (kVA)
Three-phase: S = 3.33 · f · B_m · A_i · A_w · K_w · δ · 10⁻³ (kVA)

- A_i = net iron area (m²), A_w = window area (m²), K_w = window space factor, δ = current density (A/m²). [UNVERIFIED; from a student design text excerpt, not the primary source]
- Units in the excerpt: A_i and A_w in m², δ in A/m², giving kVA with the 10⁻³ factor. Verify dimensionally before coding.

### 2.3 Empirical core sizing (K√kVA)

- Empirical form: core cross-section A_c ≈ K · √(kVA) with K chosen by flux density, frequency and steel type. K coefficient values were **not retrieved**. [UNVERIFIED]
- Per-turn voltage rule of thumb (forum, not authoritative): 0.7–0.9 · √(kVA per limb), with 0.9 preferred at 60 Hz. [VERIFIED: https://www.eng-tips.com/viewthread.cfm?qid=466927] (forum summary, low confidence)

### 2.4 Flux density selection

- Grain-oriented (GO) silicon steel: saturation ~1.9 T; practical design limit ~1.6–1.7 T at rated conditions with ~10% over-voltage allowance. [VERIFIED: forum summary, low confidence, see search result on core-design thread] Use manufacturer datasheets for real values.
- Amorphous steel: saturation ~1.5–1.6 T; stacking factor ~0.85–0.88; much lower core loss, so designs trade larger core for lower no-load loss. [UNVERIFIED]

### 2.5 Window area and current density

- Current density in windings: typically 2–3 A/mm² for liquid-filled copper; dry-type often lower. [UNVERIFIED]
- Window space factor K_w accounts for insulation, clearance, and cooling ducts. [UNVERIFIED value]

### 2.6 Winding resistance and load loss

- R = ρ · l / A_cond, with ρ temperature-corrected: R_T = R_75 · (T_k + T)/(T_k + 75) for copper (T_k ≈ 234.5 °C). [UNVERIFIED]
- Load (I²R) loss: P_LL,dc = I² · R. Add stray/eddy loss. [UNVERIFIED]
- Stray/eddy loss: P_EC = P_EC,R · Σ(I_h/I_1)² · h². [VERIFIED: C57.110 model summary in Section 1.4 search result; IEEE model] Use C57.110 for harmonic derating.

### 2.7 No-load (core) loss

- Core loss from steel loss curves (W/kg vs B at frequency), multiplied by core mass, plus joint/corner allowances. [UNVERIFIED]
- Amorphous loss curve must come from the supplier. [UNVERIFIED]

### 2.8 Efficiency and regulation

- Efficiency: η = S·x·PF / (S·x·PF + P_NL + x²·P_LL) with x = load fraction of rated kVA. [UNVERIFIED; standard form]
- Maximum efficiency at x = √(P_NL / P_LL). [UNVERIFIED]
- Regulation: ΔV% ≈ x·(R_pu·PF + X_pu·sinθ) + ... (second-order term). [UNVERIFIED]

### 2.9 Percent impedance from leakage reactance

- Z% = 100 · I_rated · Z / V_rated.
- Leakage reactance for concentric windings (Rogowski form): X = 2π f μ₀ N² (MLT / H) · K_R · (a_leak) — where MLT = mean length of turn, H = winding height, a_leak = leakage-path dimension, K_R = Rogowski factor correcting for end-flux fringing. [UNVERIFIED; exact K_R expression not confirmed]
- A 2021 analytic paper gives a leakage-reactance formula using Rogowski's height for wound-core transformers, validated by FEM and measurements. [VERIFIED: https://content.iospress.com/articles/international-journal-of-applied-electromagnetics-and-mechanics/jae190140] (abstract only; formula not read)
- Percentage impedance is a voltage drop expressed as a fraction of rated voltage. [VERIFIED: https://www.electricalvolt.com/percentage-impedance-of-transformer-and-its-calculation/] (summary)
- Standard textbook references to check: Kulkarni & Khaparde, *Transformer Engineering* [title VERIFIED via search; contents UNVERIFIED]; Georgilakis, *Spotlight on Modern Transformer Design*; Austen Stigant & Franklin, *J&P Transformer Book*. [UNVERIFIED]

---

## 3. Temperature rise and thermal

### 3.1 Limits

- Dry-type (C57.96 1999 edition per search): average winding rise 80 °C, 115 °C, 150 °C; hot-spot max 150 °C, 180 °C (or 185 °C per 1989 edition), 220 °C. The 220 °C class pairs with a 150 °C average rise. [VERIFIED: https://store.sfs.fi/en/ieee-c5796-1999] (search summary) and [VERIFIED: https://store.sfs.fi/en/ieee-c5796-1989]
  - The 1989 vs 1999 editions disagree on the middle hot-spot value (185 vs 180 °C). Check the edition in force.
- Liquid-filled (C57.12.00 / C57.91): average winding rise 65 °C; top-oil rise 65 °C (standard); hot-spot rise 80 °C above ambient for 65 °C-rise units. [UNVERIFIED]
- C57.91-2011 loading guide limits cited by secondary source: top-oil 120 °C and hot-spot 200 °C as loading safety limits. [VERIFIED: search summary, paper not checked]

### 3.2 Hottest-spot model (C57.91 style)

θ_H = θ_A + Δθ_TO + Δθ_H

- θ_A = ambient, Δθ_TO = top-oil rise over ambient, Δθ_H = hot-spot rise over top oil. [UNVERIFIED]
- Top-oil and hot-spot rise follow exponential responses with oil and winding time constants. [UNVERIFIED]

### 3.3 Aging (C57.91)

- Aging acceleration factor (one source, C57.91 form): F_AA = exp[15000/383 − 15000/(θ_H + 273)], with θ_H in °C. 383 corresponds to a 110 °C reference. [VERIFIED: search summary of IEEE PES minutes / papers; primary not retrieved]
- Equivalent aging over a load cycle: F_EQA = Σ(F_AA · Δt) / Σ(Δt). [UNVERIFIED form; check C57.91]
- Percent loss of life: %LOL = F_EQA · t / (normal insulation life) × 100. A secondary source cites normal life of 180,000 h for distribution transformer insulation. [VERIFIED: secondary summary; primary not checked]
- Moisture and oxygen correction: 2005 committee minutes note the original aging equations were based on sealed-tube tests with low moisture (<0.5%). A proposal to apply moisture/oxygen multipliers to F_AA was made; not confirmed in the final C57.91 text. [VERIFIED: https://grouper.ieee.org/groups/transformers/meetings/f2005_memphis/Minutes/F05-ILSC.pdf] (search summary)

---

## 4. Short-circuit withstand

- Categories I–IV per C57.12.00 (see Section 1.3). Table not retrieved.
- Through-fault duration: 2 s is the usual withstand basis. [UNVERIFIED]
- Axial and radial forces: F ∝ I² (peak current squared). Peak asymmetrical current uses k_asym ≈ 1.8 (X/R dependent). [UNVERIFIED]
- Protection: C57.109 coordinates protective device curves with transformer damage curves. [VERIFIED: https://online.standard.no/en/ieee-c57109] (scope)

---

## 5. Application sizing

### 5.1 Full-load current

I_FL = S / (√3 · V_LL) for three-phase; I_FL = S / V for single-phase. [UNVERIFIED; standard]

### 5.2 Short-circuit current at secondary

I_sc = I_FL / Z_pu, with Z_pu = %Z / 100 (on transformer base). [UNVERIFIED; standard]
- Infinite-bus assumption: source impedance neglected. Include upstream impedance for real studies.

### 5.3 Load sizing factors

- Continuous load: size to continuous kVA; 65 °C-rise typically OK to 100% continuous. [UNVERIFIED]
- Motor starting: inrush and voltage dip; check against motor inrush multiples (typically 6–8× FLA; UNVERIFIED).
- Harmonics: use C57.110 derating or K-factor per C22.2 No. 47 TIL I-28. [VERIFIED: https://webstore.ansi.org/standards/csa/csac22472013r2018]
- Transformer inrush: typically 8–12× rated for the first cycles; decays over seconds. [UNVERIFIED]

### 5.4 Standard kVA ratings, impedances, and taps

- Standard kVA steps (25, 37.5, 50, 75, 112.5, 150, 225, 300, 500, 750, 1000, 1500, 2000, 2500 kVA, etc.). [UNVERIFIED; check C57.12.00 Table]
- Standard %Z values (e.g., 5.75% for distribution units; 7.0% for padmount; higher for large power). [UNVERIFIED]
- Taps: typically ±2×2.5% HV taps for distribution units. [UNVERIFIED]

---

## 6. Design software and tools

| Tool | Type | What it does | Tag |
|---|---|---|---|
| FEMMT (FEM Magnetics Toolbox) | Open source, Python | Generates FEM models for transformers/inductors (2- and n-winding), litz wire, core databases. Needs Python 3.10+ and ONELAB. GUI experimental. | [VERIFIED: https://pypi.org/project/femmt/] |
| FEMM | Free 2D magnetostatic/eddy solver | Used for transformer sheet/equivalent-circuit work. Geometry built by hand. | [VERIFIED: search summary of Paderborn/ FEMM use] |
| ANSYS Maxwell | Commercial 3D FEA | Transformer inductance and field analysis; compared with COMSOL in Sandia report | [VERIFIED: https://www.sandia.gov/research/publications/details/transformer-analysis-with-ansys-maxwell-and-comsol-2023-01-31/] |
| COMSOL AC/DC | Commercial multiphysics | Transformer analysis, magnetic formulation, thermal coupling | [VERIFIED: https://www.comsol.com/video/analyzing-transformer-designs-using-comsol-multiphysics] |
| Simcenter MAGNET, JMAG, specialist transformer packages (e.g., SEE/Elgraph-type) | Commercial | Not searched in this session | [UNVERIFIED] |
| In-house design spreadsheets/codes | Manufacturer | Output equation, loss, impedance; typical of manufacturers | [UNVERIFIED] |

Licensing: Maxwell and COMSOL are paid; academic/student terms not confirmed. [UNVERIFIED]

---

## 7. Preliminary design algorithm (for implementation)

### 7.1 Inputs
- S (kVA), phases (1 or 3), f (Hz), V_HV, V_LV (line-to-line), connection, cooling (AN/AF/ONAN/AA/dry-AN/AFA), temperature class (65 °C rise liquid; 80/115/150 °C dry), steel type (GO or amorphous), target %Z, target temperature/ambient, DOE/CSA efficiency tier, short-circuit category.

### 7.2 Steps (sketch; all constants UNVERIFIED)
1. **Currents:** I_HV = S/(m·V_HV), I_LV = S/(m·V_LV), m = 1 or √3 factor per convention.
2. **Core flux:** choose B_m (GO ~1.6–1.7 T; amorphous ~1.5 T, to datasheet). Choose stacking factor (GO ~0.95, amorphous ~0.85–0.88).
3. **Core area:** from output equation (Section 2.2) with assumed K_w and δ; or K√kVA start point. Iterate.
4. **Turns:** N_LV = V_LV / (4.44 · f · B_m · A_c); N_HV = N_LV · V_HV / V_LV (round to integer, adjust B).
5. **Conductor:** A_cond = I / δ; select standard wire/foil size; check window fits (K_w).
6. **Winding resistance:** R at 75 °C; compute P_DC.
7. **Eddy/stray loss:** P_EC from C57.110 model or ratio to P_DC; P_stray estimate.
8. **No-load loss:** core mass × loss/kg at B_m, f; add corner/joint allowance.
9. **Impedance:** Rogowski leakage reactance (Section 2.9), %Z; compare to target.
10. **Efficiency:** η at 50%, 75%, 100% load using Section 2.8; compare to DOE 10 CFR 431.196 (or C802.2 for Canada).
11. **Temperature:** top-oil rise and hot-spot per C57.91 (liquid) or C57.96 (dry); check against class limit.
12. **Short-circuit check:** I_sc = I_FL/Z_pu; compare with C57.12.00 category; compute forces.
13. **Output:** report kVA, turns, conductor, core dims, losses, %Z, efficiency, temp rise, DOE pass/fail.

### 7.3 Pseudo-code (for a programmer, placeholders only)

```
inputs: S_kVA, phases, f, V_HV, V_LV, cooling, class, steel
I_LV = S/(m*V_LV); I_HV = S/(m*V_HV)
B = Bm_table[steel]; kf = stack[steel]
A_core = solve_output_eqn(S, f, B, kw, delta)   # Section 2.2, iterate
N_LV = V_LV/(4.44*f*B*A_core*kf); N_HV = N_LV*V_HV/V_LV
...
Z_pu = leakage_reactance(...) (Rogowski)       # UNVERIFIED
eta = efficiency_curve(P_NL, P_LL)
pass_DOE = eta >= doe_min(S, phases)           # table not yet loaded
```

Note: the DOE minimum efficiency lookup needs the Tables I.1–I.3 from the 2024 rule (not retrieved).

---

## Sources

Verified (retrieved or in search results this session):
- https://standards.ieee.org/standard/C57_12_00-2021.html
- https://standards.ieee.org/ieee/C57.12.90/4559
- https://grouper.ieee.org/groups/transformers/notices/C57-2002%20contents.pdf
- https://standards.ieee.org/standard/C57_96-2013.html
- https://standards.ieee.org/ieee/C57.96/10554/
- https://standards.ieee.org/standard/C57_109-2018.html
- https://standards.ieee.org/ieee/C57.109/12481
- https://online.standard.no/en/ieee-c57109
- https://infostore.saiglobal.com/en-us/Standards/IEEE-C-57-110-2008-571403_SAIG_IEEE_IEEE_1307743/
- https://powerquality.blog/2024/09/13/an-introduction-to-transformer-harmonic-current-derating-metrics/
- https://www.govinfo.gov/content/pkg/FR-2024-04-22/html/2024-07480.htm
- https://www.powermag.com/doe-proposes-new-distribution-transformer-standards-as-crippling-shortages-persist
- https://public-inspection.federalregister.gov/2026-11971.pdf
- https://scc-ccn.ca/standards/notices-of-intent/csa-group/minimum-efficiency-values-dry-type-transformers-0
- https://webstore.ansi.org/standards/csa/csac80218r2023
- https://ccn-scc.ca/standardsdb/standards/4007539
- https://scc-ccn.ca/standardsdb/standards/4027191
- https://webstore.ansi.org/standards/csa/csac22472013r2018
- https://ccn-scc.ca/standardsdb/standards/4003379
- https://www.csagroup.org/store/product/2700509
- https://americas.hammondpowersolutions.com/resources/faq/definition/what-is-ul-1561
- https://americas.hammondpowersolutions.com/resources/faq/definition/what-is-ul-1562
- https://standards.globalspec.com/std/14541976/ul-1561
- https://standards.globalspec.com/std/14543333/ul-1562
- https://datasheets.globalspec.com/ds/uls/ul-506/dbaaaa5f-1a2d-4c28-b5d5-c5849ccc00be
- https://store.sfs.fi/en/ieee-c5796-1999
- https://store.sfs.fi/en/ieee-c5796-1989
- https://grouper.ieee.org/groups/transformers/meetings/f2005_memphis/Minutes/F05-ILSC.pdf
- https://content.iospress.com/articles/international-journal-of-applied-electromagnetics-and-mechanics/jae190140
- https://www.electricalvolt.com/percentage-impedance-of-transformer-and-its-calculation/
- https://pypi.org/project/femmt/
- https://www.sandia.gov/research/publications/details/transformer-analysis-with-ansys-maxwell-and-comsol-2023-01-31/
- https://www.comsol.com/video/analyzing-transformer-designs-using-comsol-multiphysics
- https://www.eng-tips.com/viewthread.cfm?qid=466927 (forum, low confidence)

Not retrieved (needed to upgrade UNVERIFIED items): C57.12.00 Table (categories, impedances, kVA steps); C57.91-2011 full text; C57.96 current/draft; C57.12.01/C57.12.91; C57.12.34/36; C57.12.80; DOE 10 CFR 431.196 Tables I.1–I.3; CSA C802.2 Table 1; C802.1; C88; Kulkarni & Khaparde text.

---

## Open questions / needs checking

1. **DOE tables:** Pull Tables I.1–I.3 of the 2024 final rule (govinfo HTML was truncated at 100k chars; read further using offset). Build the efficiency lookup from them.
2. **DOE 2026 RFI:** Confirm whether DOE has changed the April 23, 2029 compliance date after the EERE-2026-BT-STD-0133 RFI (comments closed July 15, 2026).
3. **C57.12.00 Categories I–IV:** Obtain the category kVA ranges, withstand durations, and impedance tables from the current edition. My recollected kVA ranges above are unverified.
4. **C57.96 status:** Current edition is inactive; check the PC57.96 draft status and whether the 180/185 °C middle-class value changed.
5. **C57.91 equations:** Confirm F_AA, the moisture/oxygen correction, and the normal insulation life value against the published C57.91-2011 text.
6. **Rogowski factor:** Confirm the exact K_R expression and leakage-path definition from a primary text (Kulkarni & Khaparde; Georgilakis; the 2021 IOS Press paper).
7. **K-coefficient for core sizing:** The book's K value and amorphous B_max/stacking factor were not found. Verify before using the K√kVA rule.
8. **C802.2 table values:** Retrieve Table 1 minimum efficiency values; check whether a newer edition beyond C802.2-18 has been published.
9. **C57.110 eddy-loss ratio and F_HL:** Confirm the exact equations; the 2018 edition was only summarized.
10. **Missing standards:** C57.12.34, C57.12.36, C57.12.80, C57.12.91, C802.1, CSA C88, and liquid-filled efficiency in Canada were not researched.
11. **Inrush and %Z standard values:** Confirm inrush multiples and standard impedance tables from C57.12.00 and manufacturer application guides.
12. **Commercial tools:** Simcenter MAGNET, JMAG, and specialist transformer packages were not researched; licensing for academic use of Maxwell/COMSOL unconfirmed.
