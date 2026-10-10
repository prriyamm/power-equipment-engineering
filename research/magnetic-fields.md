# Magnetic Fields and Magnetically Induced Effects Around Busbars, Cable Bus and Transformer Leads

Status: research notes, 2026-10-10. Not reviewed by a licensed engineer. Standards values must be checked against the current published editions before use in any design, compliance, or customer document.

Tag key:
- [VERIFIED: URL] = read from a fetched primary or near-primary document (URL given).
- [DERIVED] = worked out here from first principles; the derivation is shown so it can be re-checked.
- [UNVERIFIED] = from a search snippet, a secondary/forum/vendor source, or general knowledge not checked against a source.

---

## 0. Summary

1. **Far-field magnitude of a balanced three-phase bar set is simple.** For balanced phasor currents on three parallel conductors with adjacent spacing s (flat or trefoil), the net current is zero, so the far field is dipole-like and falls as 1/d². The magnitude is B_rms ≈ (μ0 I / 2π) · √3 · s / d². The prompt's formula is correct [DERIVED]. The same √3·s result holds for a trefoil with side length s [DERIVED].
2. **ICNIRP 1998 values are verified; ICNIRP 2010 values are not.** The fetched ICNIRP 1998 Tables 6/7 give 60 Hz B-limits of about 417 µT (occupational) and 83 µT (public). The 2010 values usually quoted (1000 µT occupational, 200 µT public at 50/60 Hz) appear only in secondary summaries and need checking against the 2010 paper.
3. **IEEE C95.6-2002 numbers are unresolved.** A secondary source reads 904 µT as the public head-and-torso limit (equal to 9040 mG). The occupational figure is ambiguous (2.71 mT per the same garbled source). C95.6 is superseded (IEEE C95.1-2019 is current) [UNVERIFIED].
4. **IEEE 605 short-circuit force equations are verified** (EPRI 1024226 summary of IEEE 605-2008): F = 16·Γ·I_sc² / (10⁷·D) N/m with I_sc in A rms, and the bracing correction F_corr = Df²·Kf·F [VERIFIED: local copy of EPRI Technical Update 1024226, Dec 2012; original URL not captured].
5. **Not yet researched or only partly researched:** ACGIH TLVs, Health Canada guidance, CSA C22.1 Rule 12-904 text, NEC 300.20 primary text, CDA busbar skin/proximity tables, Dwight curves, eddy-loss heating in steel, and substation applicability of IEEE 644. See Section 11.

---

## 1. Magnetic flux density from straight conductors (Biot-Savart / Ampère)

### 1.1 Single long straight conductor (infinite line)

Ampère's law gives, for a long straight conductor carrying current I (A) with the field observed at radial distance r (m) outside a round conductor:

    B = μ0 I / (2π r)   [T]      with μ0 = 4π × 10⁻⁷ T·m/A

Numerically: B (µT) = 0.2 · I (A) / r (m). For example, 1000 A at 0.5 m gives 400 µT [DERIVED from the standard μ0 value; the Ampère-law form itself is UNVERIFIED against a fetched textbook].

The IEEE 605 document uses the same expression for the force between conductors, and states the Biot-Savart basis for it [VERIFIED: EPRI 1024226 summary of IEEE 605-2008, eq. 1.2].

### 1.2 Finite-length conductor (Biot-Savart)

    B(r) = (μ0 I / 4π) ∫ (dl × r̂) / |r|²

For a finite straight segment, integrating over the segment gives the familiar two-angle form B = (μ0 I / 4π d)(sin θ2 − sin θ1), where d is the perpendicular distance and θ1, θ2 are the angles to the ends [UNVERIFIED textbook result; check against a textbook such as Hayt/Griffiths]. Finite length matters near bar ends and bends (the "corner effect" that IEEE 605 excludes from its closed-form force equation, see Section 6).

### 1.3 Superposition for multiple conductors

The field at a point is the vector sum of the contributions of each conductor. For line currents in the xy-plane (2D), the field is perpendicular to the plane:

    B(P) = (μ0/2π) Σ_k I_k · ẑ × (P − P_k) / |P − P_k|²

where P_k is the position of conductor k and I_k its (phasor) current. Sum vectors, not magnitudes.

### 1.4 Three-phase balanced currents: phasor form and the far field

Let the phasors be Î_a, Î_b, Î_c (rms or peak, but use one convention throughout) with Î_a + Î_b + Î_c = 0 for balanced currents. Write the 2D complex position of each conductor as z_k. The field from a line current at z_k is conjugate-proportional to 1/(z − z_k), so the total can be expanded as:

    Σ_k Î_k / (z − z_k) = (Σ_k Î_k)/z + (Σ_k Î_k z_k)/z² + ...

With balanced currents the first term vanishes, and the leading far-field term is the "dipole" term p̂ = Σ_k Î_k z_k, giving:

    |B̂| ≈ (μ0 / 2π) · |p̂| / d²      (d = distance to the bar set, d >> s)

**Flat (horizontal) arrangement.** Place the three conductors at z = −s, 0, +s, with phasors Î_a = I, Î_b = I·e^(−j120°), Î_c = I·e^(+j120°). Then

    p̂ = s (Î_c − Î_a) = s I (−1.5 + j 0.866),   |p̂| = √3 · s · I

so the far-field rms magnitude is:

    B_rms ≈ (μ0 I / 2π) · √3 · s / d²   [DERIVED; matches the prompt's formula]

The same magnitude follows for the opposite phase sequence, since only the sign of the imaginary part changes.

**Trefoil arrangement.** Place the three conductors at the vertices of an equilateral triangle with side s, so the circumradius is R = s/√3, at angles 90°, 210°, 330°. Then Σ Î_k e^(jθ_k) = 3·e^(j90°), so |p̂| = 3R = √3·s [DERIVED]. The trefoil and flat arrangements therefore have the same far-field magnitude for the same conductor spacing s. Their near fields differ, and the trefoil's field is more symmetric.

**Caveat on the far-field form.** The field at a point is generally elliptical in time, so |B̂|/d² is a representative magnitude, not the peak field everywhere. The ellipse is found from the phasor vector B̂ = U + jV, where U and V are real 2D vectors (Re and Im parts):

    B_peak² (max over the cycle) = ½(U·U + V·V) + ½ sqrt( (U·U − V·V)² + 4 (U·V)² )

This is the largest eigenvalue of the Gram matrix of U and V [DERIVED]. Use this for compliance peaks; use |B̂| only for a quick estimate.

Validity: the far-field form needs d several times larger than s (typically d > 3–5 s). For closer points, evaluate the full sum in Section 1.3.

### 1.5 Rectangular busbar cross-section

Treat each busbar as a set of N filaments distributed over the cross-section, with each filament carrying I/N for a uniform current density J = I/A. The field outside a bar is the sum over filaments of the line-current expressions above. For points outside the bar at distances much greater than the bar thickness, a single line current at the centroid is adequate for B, though the near field needs the filament sum [DERIVED; standard approach, UNVERIFIED against a specific source].

Inside the bar, the field from a uniformly distributed current is B = μ0 J r / 2 in the azimuthal direction for a round bar, and is found from the filament sum for a rectangle [UNVERIFIED; check a textbook].

### 1.6 Multiple parallel conductors per phase

Each phase is a set of parallel conductors with currents shared among them. Treat each conductor as its own line current and use the same superposition. Current sharing is not necessarily equal: it depends on the impedance of each path, which is set by the proximity effect (Section 5). Use the actual per-conductor current distribution, not I/n, when precision matters.

---

## 2. Practical approximations for busbar field

| Quantity | Formula | Status |
|---|---|---|
| Single conductor, B at distance r | B = μ0 I / 2πr = 0.2·I/r µT | Standard physics [UNVERIFIED source] |
| Balanced 3-phase flat, far field | B ≈ (μ0 I / 2π)·√3·s/d² | [DERIVED, Section 1.4] |
| Balanced 3-phase trefoil, far field | B ≈ (μ0 I / 2π)·√3·s/d² (s = side length) | [DERIVED, Section 1.4] |
| Two-conductor force per length (peak) | F = μ0 I1 I2 / (2πd) = 2×10⁻⁷ · i1·i2 / d | [VERIFIED: consistent with EPRI 1024226 eq. 1.2] |

Practical note for the flat formula: 0.2 µT·√3 ≈ 0.346 µT per (A·m/m²). In units: B (µT) ≈ 0.346 · I (A) · s (m) / d² (m²). Check: for I = 1000 A, s = 0.2 m, d = 2 m: B ≈ 0.346 × 1000 × 0.2 / 4 ≈ 17 µT (rms).

Near-field caveat: for a finite-length run, the infinite-length result overestimates B near the ends by a few percent to tens of percent depending on geometry. Use Biot-Savart with finite segments (Section 1.2) for compliance boundaries near ends.

---

## 3. Exposure limits (60 Hz magnetic flux density)

### 3.1 ICNIRP 1998 (fetched and verified)

[VERIFIED: https://www.icnirp.org/cms/upload/publications/ICNIRPemfgdl.pdf — ICNIRP 1998 guidelines, Health Physics 74(4):494-522]

Table 6 (occupational) and Table 7 (general public), for 0.025–0.82 kHz (B-field reference level, rms):

| Group | Reference level | At 50 Hz | At 60 Hz |
|---|---|---|---|
| Occupational | B = 25/f mT | 500 µT | ≈ 417 µT |
| General public | B = 5/f mT | 100 µT | ≈ 83 µT |

Basic restrictions and reference levels are different things. Reference levels are the external-field values used for screening; basic restrictions apply to induced fields in the body. Compliance with the reference levels generally demonstrates compliance with the basic restrictions. The 1998 guidelines are superseded by the 2010 guidelines.

### 3.2 ICNIRP 2010 (NOT verified against the primary paper)

Commonly quoted values are 1000 µT occupational and 200 µT general public at 50 and 60 Hz (1 Hz–100 kHz range). [UNVERIFIED: secondary summaries only, e.g. https://networktasman.co.nz/?p=3223 and https://www.ucy.ac.cy/emfmap/?p=1782 as seen in search snippets; the emfs.info and ICNIRP PDF pages returned HTTP 403 or an expired certificate on fetch.] The public-to-occupational factor is commonly stated as 5 in 2010 (2 in one case) [UNVERIFIED]. The prompt's values (200 µT public / 1000 µT occupational) are consistent with these secondary sources but must be checked against Health Physics 2010 before use.

Important: the 2010 public level (200 µT) is about twice the 1998 level (100 µT) at 50 Hz. Do not mix the editions in a single document.

### 3.3 IEEE C95.6-2002 and IEEE C95.1-2019

- IEEE C95.6-2002 is the IEEE standard for 0–3 kHz exposure. A secondary summary reads the head-and-torso public limit as 904 µT (9040 mG), and a controlled-environment head-and-torso limit as about 2.71 mT [UNVERIFIED: garbled table, https://www.psc.nd.gov/webdocs/case/11-0696/057-010.pdf and https://emfs.info/limits/limits-organisations/ices-2002/ (403 on fetch)].
- The "9040" figure in the prompt appears to be the public head-and-torso value in mG, not an occupational value in µT. Do not use "9040 µT" as an occupational limit without checking Table 2 of the standard [UNVERIFIED].
- IEEE Xplore marks C95.6-2002 as superseded. The current IEEE standard for human exposure is C95.1-2019 (3 kHz–300 GHz) [UNVERIFIED: search snippet only, https://ieeexplore.ieee.org/document/1046043/footnotes]. Check its low-frequency magnetic limits directly.

### 3.4 ACGIH TLVs and Health Canada

Not yet researched. ACGIH's 2026 TLV entries for ELF magnetic fields and Health Canada's Safety Code 6 (which uses ICNIRP-style values) need separate lookup. See Section 11.

### 3.5 Practical design implication

Using the far-field formula in Section 2 (B ≈ 0.346·I·s/d² µT), the 1998 public reference level of about 83 µT at 60 Hz is reached, for example, at d ≈ √(0.346·I·s/83) m. For I = 1000 A and s = 0.2 m, that is d ≈ 0.9 m. Compliance decisions need the actual edition, the actual exposure category, and the exposure time, not a single number.

---

## 4. Measurement: IEEE 644

- IEEE 644-2019 is the current IEEE procedure for measuring power-frequency electric and magnetic fields and calibrating the meters [VERIFIED: https://store.sfs.fi/en/ieee-644-2019 catalog listing; 1994 edition superseded, 1987 edition withdrawn per same listing].
- Stated scope is ac overhead power lines, with procedures for measurements at ground level [VERIFIED: search snippet on the same catalog and PDF listing].
- Applicability to substations or indoor busbars is not established. The standard may be usable with caution for busbar work, but this has not been checked against the full text [UNVERIFIED].

---

## 5. Induced heating, losses and conductor AC effects

### 5.1 Induced currents in ferrous enclosures and structural steel

- NEC 300.20(A): conductors of an AC circuit in ferrous enclosures or raceways must be grouped so that induction does not heat the surrounding ferrous metal. The method is to group all phase conductors (and neutral and equipment grounding conductors) together, so the fields largely cancel [UNVERIFIED: forum and magazine summaries only; the NFPA fetch returned no section text].
- Exception covers single conductors used for skin-effect heating under sections 426.42 and 427.47 [UNVERIFIED].
- 300.20(B): single conductors through ferrous plates are handled by using nonmagnetic (aluminum) locknuts and slotting holes [UNVERIFIED].
- CSA/CEC: a forum post quotes CEC Rule 12-904 ("Conductors in raceways"): all conductors of a circuit in a metal raceway shall be contained in the same raceway, and warns that a single conductor heats any ferrous material it encircles through eddy-current and hysteresis losses [UNVERIFIED: secondary quotation, https://forums.mikeholt.com/goto/post?id=1940642]. The prompt's "CEC 12-904?" reference is plausible, but the wording must be checked against CSA C22.1 directly.
- CEC Rule 4-008 (single-conductor cables above 425 A: a derating to 70% of Table 1/3 values is one listed option) [UNVERIFIED: secondary source, https://iaeimagazine.org/magazine/features/single-conductor-issues].

Practical rule (engineering judgment, UNVERIFIED): keep all phases of a circuit in one steel enclosure or use nonmagnetic (aluminum, stainless) enclosures or gland plates; cut slots between conductor penetrations in steel plates; and check hot-spot temperatures on steel near high-current runs.

### 5.2 Eddy-current heating estimate

Power per unit volume in a conducting plate in a sinusoidal field is roughly P ∝ σ · ω² · B² · t² (thin plate, t thickness), with σ conductivity and ω angular frequency. Ferrous steel adds hysteresis loss, which is nonlinear in B [DERIVED form; coefficient and loss model UNVERIFIED]. A FEM model (Section 7) is needed for any quantitative heating prediction.

### 5.3 Skin and proximity effects in busbars (AC/DC resistance ratio)

- Skin effect: current concentrates at the conductor surface at AC, raising AC resistance above DC. The skin-effect ratio R_ac/R_dc > 1 defines the significance [UNVERIFIED: vendor blog https://industrialmonitordirect.com/tr/blogs/knowledgebase/calculating-skin-effect-ratio-for-rectangular-busbar-conductors].
- Proximity effect: parallel flat bars for the same phase enhance the effect, and adjacent phase bars also redistribute current [UNVERIFIED: simulation vendor summary, https://www.emworks.com/application/thermo-structural-behavior-of-three-phase-busbar-system-under-ac-magnetic-regime].
- An illustrative figure in a secondary source gives a skin ratio of about 1.27 at x ≈ 94 (133 Hz), citing a CDA rectangular-conductor table [UNVERIFIED].
- Dwight curves: not verified. Their x-parameter definition and exact formulas are not confirmed here. Use the CDA *Copper Busbar* design guide or IEEE/NEMA ampacity methods as the primary source, after checking they are the current editions.

### 5.4 Recommended clearances and spacing

Not researched. Typical practice (enclosure clearance, phase-to-phase spacing for the force limits in Section 6, and steel-to-bus clearances) must come from the manufacturer's standards and the CDA/IEEE documents. Flagged as an open item.

---

## 6. Short-circuit electromagnetic forces

### 6.1 Basic force (IEEE 605-2008 eq. basis)

[VERIFIED: EPRI Technical Update 1024226 (Dec 2012), summary of IEEE 605-2008 clause 11.3]

For parallel infinitely long conductors with symmetrical RMS fault current I_sc (A rms), center-to-center spacing D (m), and fault-type constant Γ:

    F_sc = 16 · Γ · I_sc² / (10⁷ · D)   [N/m]

This follows from the textbook F = μ0 I1 I2 / (2πd) with the peak asymmetrical current I_peak = 2√2·I_sc (K = 2√2 for infinite X/R). Γ = 1 for a line-to-line or single-phase fault; other values of Γ are tabulated in IEEE 605-2008 Table 13 [VERIFIED: EPRI 1024226].

Check against the prompt's formula: with peak current i (A), F = 2×10⁻⁷ i²/d [N/m]. Using i = 2√2·I_sc gives F = 1.6×10⁻⁶ I_sc²/d = 16 I_sc²/(10⁷ d), which matches the IEEE form at Γ = 1 [DERIVED].

Note that the prompt's F = 2×10⁻⁷ i²/d is the instantaneous force for peak current i. The time-averaged value for sinusoidal current is half of that. Use the IEEE convention for bracing.

### 6.2 Corrected force for bracing

[VERIFIED: EPRI 1024226 eq. 1.6–1.8]

    F_corr = Df² · Kf · F_sc

- Df is the half-cycle decrement factor, a function of the circuit time constant T_a = X/(2πf·R) (EPRI 1024226 eq. 1.7). The exact Df expression (EPRI eq. 1.8) must be copied from IEEE 605-2008, not from this note.
- Kf is the mounting-structure flexibility factor (IEEE 605-2008 Fig. 2-2).
- The closed-form approach excludes unequal bus spans, a change of bus direction, and corner effects; use another method for those cases [VERIFIED: EPRI 1024226 section 2].

### 6.3 Dynamic response and conservatism

- The standard treats the force as a static load applied in phase with the force. The real bus response can be dynamic and lower or higher depending on natural frequency [VERIFIED: EPRI 1024226].
- EPRI describes IEEE 605 as conservative in most cases, and a CIGRE-based dynamic approach may be more realistic for some structures [VERIFIED: EPRI 1024226 summary; the 2008 vs 1998 magnitude claim is from a vendor blog and UNVERIFIED].

### 6.4 Switchgear bracing (ANSI C37.20.x)

Not researched. Switchgear bus bracing ratings are set by ANSI C37.20.x (for metal-enclosed switchgear) and IEC/UL equivalents for the Canadian and US markets. The rating is the peak asymmetrical current the bus can withstand, and the bracing force is derived from it. Flagged as open.

---

## 7. Open-source / programmable tools

| Tool | What it does | Source status |
|---|---|---|
| FEMM (Finite Element Method Magnetics) | Magnetostatic and low-frequency time-harmonic magnetic problems, electrostatics, heat flow, current flow. 2D planar and axisymmetric. Scriptable with Lua. | [VERIFIED: https://www.femm.info/wiki/HomePage for solver list; https://femm.info/wiki/Manual (search snippet) for time-harmonic and Lua scripting]. The manual dates from around 2013 and may not match later releases. |
| pyFEMM (Python wrapper for FEMM) | Python interface to FEMM's Lua API. | [UNVERIFIED: no pyFEMM API docs were fetched. Confirm function names on the PyPI project page.] |
| Elmer FEM | Multiphysics FEM (magnetodynamics, heat, structural). Time-harmonic AV solver, harmonic power loss in the 2D magnetodynamics module, complex reluctivity, and a Bertotti core-loss model in release 9.0. Native Linux build is fastest. | [VERIFIED-secondary: FreeCAD Elmer wiki https://wiki.freecad.org/FEM_EquationMagnetodynamic and Elmer 9.0 release notes on https://zenodo.org/records/7892181 (search snippets)]. The Elmer Models Manual was not fetched. |
| magpylib | Python library for analytic magnetic fields from magnets and current sources, vectorized, computes forces and torques. | [VERIFIED: https://magpylib.readthedocs.io/en/latest/ for analytic B-field and current sheet sources]. Line-current source support is not confirmed on that page [UNVERIFIED]. |
| scikit-fem | Pure-Python finite element assembly library (sparse matrices with SciPy). Triangles, quads, tets, hexes; Nédélec and Raviart-Thomas elements. Does not provide a ready-made magnetostatic solver; you must write the weak form. | [VERIFIED-secondary: https://scikit-fem.readthedocs.io/en/latest/index.html and PyPI listing (search snippets)] |

Recommendation for this project: use magpylib or the analytic formulas for quick far-field and filament sums; use FEMM (with pyFEMM) for 2D cross-sections with steel and eddy losses in time-harmonic mode; use Elmer for 3D or harmonic loss work that FEMM cannot handle.

---

## 8. Algorithm for B-field mapping around a conductor geometry

Input: conductor list (position, dimensions or filament count, phasor current, phase), grid of observation points, frequency, mode (rms or peak).

1. Choose a convention: rms or peak. Keep it for every current, field and force.
2. Build a filament model of each conductor. For a rectangular bar of width w and thickness t, use an N_w × N_t grid of filaments (for example 10×3). Assign each filament the bar's current divided by its count. Use the actual per-conductor current split for parallel conductors (Section 1.6).
3. Compute each phase phasor Î_k from the given rms magnitude and angle (for example Î_a = I∠0°, Î_b = I∠−120°, Î_c = I∠+120°).
4. For each observation point P (2D plane or 3D grid):
   a. For each filament k, compute the unit-current field vector G_k(P) = (μ0/2π) · ẑ × (P − P_k) / |P − P_k|² (2D) or the Biot-Savart integral for finite-length 3D segments (Section 1.2).
   b. Sum the phasor field: B̂(P) = Σ_k Î_k G_k(P). Keep the result as a complex 3-vector (or 2-vector for 2D).
   c. Split into real and imaginary parts: U = Re{B̂}, V = Im{B̂}.
   d. Compute the peak magnitude over the cycle: B_peak² = ½(U·U + V·V) + ½ √((U·U − V·V)² + 4 (U·V)²). For rms, divide by √2.
5. Output maps: |B| (µT) on the plane, with contours at the reference levels (for example 83 µT and 200 µT for 60 Hz from the sources in Section 3; confirm the edition before use).
6. Check the far-field estimate from Section 1.4 at a few distances as a sanity test. Mismatches usually mean a units error (mT vs µT) or a sign error in the phasor angle.
7. Force (for bracing): for each conductor pair, F_kl = (μ0 / 2π) · I_k · I_l / d_kl (per unit length, peak currents), and resolve by vector direction. Apply the IEEE 605 correction factors (Section 6.2) for design.
8. Validate against a FEM run (FEMM, 2D time-harmonic) for one geometry before trusting the code for compliance.

Unit tests to include: single wire (B = 0.2 I/r µT); balanced three-phase far-field (compare with √3·s·I·μ0/(2π d²)); symmetric trefoil (|p̂| = √3·s).

---

## 9. Sources

Verified (fetched, or search result read in full):
- ICNIRP 1998 guidelines, Health Physics 74(4):494-522, Tables 6 and 7 — https://www.icnirp.org/cms/upload/publications/ICNIRPemfgdl.pdf
- EPRI Technical Update 1024226, "Reevaluation of IEEE Standard 605's Calculation of Short Circuit Force on Rigid Busbar Structures" (Dec 2012), summary of IEEE 605-2008 clause 11.3 — local copy; original URL not captured
- FEMM homepage — https://www.femm.info/wiki/HomePage
- Magpylib documentation — https://magpylib.readthedocs.io/en/latest/
- IEEE 644-2019 catalog listing — https://store.sfs.fi/en/ieee-644-2019
- scikit-fem documentation — https://scikit-fem.readthedocs.io/en/latest/index.html

Secondary, read only as search snippets or forum/vendor pages (treat as UNVERIFIED):
- ICNIRP 2010 summaries — https://networktasman.co.nz/?p=3223 ; https://www.ucy.ac.cy/emfmap/?p=1782
- IEEE C95.6-2002 garbled table — https://www.psc.nd.gov/webdocs/case/11-0696/057-010.pdf ; https://emfs.info/limits/limits-organisations/ices-2002/ (403 on fetch)
- NEC 300.20 forum summaries — https://forums.mikeholt.com/threads/induced-currents-in-ferrous-metal-enclosures-or-ferrous-metal-raceways.102507/latest ; https://forums.mikeholt.com/goto/post?id=1940642
- CEC single-conductor issues — https://iaeimagazine.org/magazine/features/single-conductor-issues
- FEMM manual — https://femm.info/wiki/Manual
- FreeCAD Elmer magnetodynamics wiki — https://wiki.freecad.org/FEM_EquationMagnetodynamic
- Elmer 9.0 release notes — https://zenodo.org/records/7892181
- Vendor busbar skin effect page — https://industrialmonitordirect.com/tr/blogs/knowledgebase/calculating-skin-effect-ratio-for-rectangular-busbar-conductors
- Three-phase busbar simulation page — https://www.emworks.com/application/thermo-structural-behavior-of-three-phase-busbar-system-under-ac-magnetic-regime
- IEEE C95.6 footnotes page (superseded status) — https://ieeexplore.ieee.org/document/1046043/footnotes

Not accessible (HTTP 403 or expired certificate on fetch): ICNIRP 2010 PDF from neuron.yale.edu (expired certificate); IEEE C95.6-2002 PDF from neuron.yale.edu (expired certificate); NFPA NEC pages (no 300.20 text); emfs.info ICNIRP 2010 page (403); copper.org publications (403); femm/pyFEMM API pages.

---

## 10. Open questions / needs checking

1. **ICNIRP 2010 values.** Confirm 1000 µT occupational and 200 µT public at 50/60 Hz, the public-to-occupational factor, and the frequency range, from Health Physics 2010 (or the ICNIRP PDF, which this run could not open).
2. **IEEE C95.6-2002 vs C95.1-2019.** Confirm which standard governs the client's jurisdiction. Confirm the 60 Hz head-torso and arms-legs B-limits, controlled and uncontrolled, from the official table. Check whether the "9040" value is mG or µT. The occupational value (2.71 mT) is unconfirmed.
3. **ACGIH TLVs and Health Canada Safety Code 6.** Not researched. Need current ELF magnetic TLV and the Health Canada limit used for public and occupational exposure.
4. **NEC 300.20 primary text.** Get the current NEC edition text for 300.20(A) and (B), and any ampacity/derating interaction.
5. **CSA C22.1 Rule 12-904 and 4-008 text.** Verify from CSA C22.1 (the current edition in force in the client's province).
6. **Dwight curves and CDA busbar tables.** Obtain the CDA *Copper Busbar* design guide (copper.org was 403 on fetch) and confirm the skin/proximity factor definitions and the rectangular-bar AC/DC ratio method.
7. **IEEE 605-2008 Df and Kf formulas and Table 13 Γ values.** Copy exact equations from the standard, not from the EPRI summary or a vendor blog. Confirm the 1998 vs 2008 magnitude difference.
8. **Switchgear bracing (ANSI C37.20.x).** Confirm the rated-withstand and bracing method used in the client's product line.
9. **IEEE 644 applicability to substations and indoor busbars.** The catalog scope is overhead lines; confirm from the full 2019 text.
10. **Ferrous heating.** Need a validated eddy-current and hysteresis loss model for steel plates near busbars (FEMM or Elmer time-harmonic run). No numeric heating model has been verified in this note.
11. **Ellipse formula (Section 1.4).** Derived here from linear algebra; check numerically against a direct simulation before using in a design tool.
12. **magpylib line-current support.** Confirm whether magpylib has a finite line-current source before relying on it for busbar fields.
13. **pyFEMM API.** Confirm function names and whether harmonic (AC) loss solves are exposed.
14. **Clearances and recommended spacing.** Not researched.
