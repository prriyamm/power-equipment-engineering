# Switchgear and Switchboard Busbar Design Calculations: Research Notes

Scope: US/Canada LV and MV switchgear and switchboards (UL, CSA, NEC, CEC; ANSI/IEEE C37 series). IEC only as comparison.

**Status of this document.** Web search was heavily rate-limited during this session (most searches returned `too_many_requests`), and several copper.org and other standards pages returned HTTP 403. Only two sources were read in full: the EPRI report on IEEE 605 (downloaded PDF, text extracted) and an Intertek comparison blog. Everything else is a search-snippet, forum, or vendor-blog claim, or general background knowledge. Those are marked **[UNVERIFIED]**. No copyrighted standard table is reproduced.

Tag legend:
- **[VERIFIED: URL]**: read in the cited document during this session.
- **[UNVERIFIED]**: from a search snippet, forum, vendor blog, or general knowledge. Check against the standard before use.

---

## 1. Product-to-standard map

| Product | Primary US standard | Canadian counterpart | Notes |
|---|---|---|---|
| Dead-front LV switchboards | UL 891 | CSA C22.2 No. 244 | UL 891 / CSA 244 / NMX-J-118/2-ANCE are described as a trinational harmonized set. Scope: nominal voltage up to 1000 V, dead-front, CEC Part I / NEC / NOM-001-SEDE. [UNVERIFIED: search snippets from https://www.orderline.com/csa-c22-2-no-244-19-national-standard-of-canada-reaffirmed-2024-switchboards and https://webstore.ansi.org/standards/csa/csac2224419r2024] |
| LV metal-enclosed power circuit breaker switchgear | UL 1558 / ANSI C37.20.1 | CSA C22.2 No. 31 (titled "Switchgear assemblies", 2023) | No source found confirming UL 1558 and CSA 31 are harmonized. [UNVERIFIED] Intertek describes UL 1558 as drawout LV power breaker switchgear with higher fault ratings and main-tie-main capability. [VERIFIED: https://www.intertek.com/blog/2026/07-29-ul-891-vs-ul-1558/] |
| MV metal-clad switchgear | ANSI/IEEE C37.20.2 | none identified | Scope described as MC switchgear 5 kV to 38 kV. [UNVERIFIED: ANSI/IEEE store listing snippet, https://webstore.ansi.org/standards/ieee/ieeec37201999r2005] |
| MV metal-enclosed interrupter switchgear | ANSI/IEEE C37.20.3 | none identified | [UNVERIFIED: general knowledge. Not searched successfully.] |
| Arc-resistant switchgear | ANSI/IEEE C37.20.7 | none identified | [UNVERIFIED: general knowledge.] |
| Panelboards | UL 67 | CSA C22.2 No. 29 (panelboards and related) | [UNVERIFIED: general knowledge for CSA 29 scope.] |
| Busway | UL 857 | CSA C22.2 No. 214 (busway) | [UNVERIFIED: CSA number from general knowledge.] |
| Metal-enclosed bus (isolated phase, nonsegregated, segregated, cable bus) | IEEE C37.23 | none identified | Covers assemblies up to 38 kV. Does **not** cover UL 857 busway. [UNVERIFIED: standards listing snippets, https://standards.ieee.org/ieee/C37.23/5577 and https://ewh.ieee.org/soc/pes/switchgear/minutes/2012-1/S12SAa5.pdf] |

**Tri-national harmonization.** CSA C22.2 No. 244 is the Canadian edition of the switchboard standard, harmonized with UL 891 and Mexico's NMX-J-118/2-ANCE. [UNVERIFIED: snippet from https://www.csagroup.org/fr/store/product/2426063/] Harmonization for the switchgear side (UL 1558 vs CSA 31) was not found.

**Design implication.** A switchboard that is bus-rated under UL 891 is not automatically a switchgear assembly under UL 1558. Short-circuit and clearance requirements differ by family, so the product family must be fixed before any calculation starts.

---

## 2. Temperature rise limits

**Status: the specific UL 891 values stated in the request (65 °C rise for silver-plated joints, 50 °C for unplated) were NOT verified.**

Evidence found:
- A forum post says the breaker terminal rise must not exceed 50 °C above ambient per UL 489. This is the breaker standard, not UL 891. It may be the origin of the "50 °C" figure. [UNVERIFIED: https://forums.mikeholt.com/goto/post?id=2675540 region]
- A forum post cites a UL 891 bus table on a current-per-square-inch basis (quoted as 1000 A/in²). The same post treats it as secondhand. [UNVERIFIED]
- Marking rule: switchboards rated 110 A or less are marked for 60 °C conductors, larger circuits for 75 °C, per NEC Table 310.15(B)(16). This is a conductor-ampacity marking rule, not a bus temperature-rise limit. [UNVERIFIED: forum quote]
- IEC 61439 comparison (35 °C ambient): copper busbars rise about 105 K (140 °C absolute), incorporated components about 90 K, terminals and external insulated conductors about 70 K. [UNVERIFIED: engineering blog, https://blog.se.com/infrastructure-and-grid/power-management-metering-monitoring-power-quality/2018/05/23/iec-61439-rated-current-of-electrical-panel-and-switchboard-protection-devices]

**Needed:** the UL 891 temperature-rise table (component, finish, and limit, with test ambient and stabilization criterion), the C37.20.1 and C37.20.2 bus and connection temperature-rise tables, and the NEC 110.14(C) terminal-temperature limits. Get these from the standards, not from this document.

---

## 3. Busbar sizing

### 3.1 Current density rules of thumb

- **NEC 366.23 (auxiliary gutters)** caps continuous current in bare copper bars at 1000 A/in² of cross-section. Aluminum is quoted at 700 A/in². This is a code limit for gutters, not a switchboard design method. [UNVERIFIED: forum quote of NEC 366.23, https://forums.mikeholt.com/threads/bus-bar-ampacity.30005/latest. Confirm against the NEC text.]
- The request's "750 A/in² aluminum" figure is **not** confirmed. The code value quoted above is 700 A/in².
- Switchboard bus is generally rated by temperature-rise testing, not by current density. [UNVERIFIED: forum opinions. Confirm against UL 891 and the manufacturer's listing data.]

### 3.2 Copper Development Association method

- CDA tables give rectangular copper bar ampacity at rises of 30, 50, and 65 °C above ambient, assuming 99% IACS conductivity. CDA recommends designing for a 30 °C rise or less for energy efficiency and says rises above 65 °C are not recommended. [UNVERIFIED: search snippet from https://copper.org/applications/electrical/busbar/bus_table3.php. The page returned HTTP 403 when fetched.]
- Shape matters. A 4 in × 1/4 in bar can carry about 23% more current than a 2 in × 1/2 in bar at the same temperature rise, despite equal cross-section. [UNVERIFIED: forum example. Verify against CDA tables.]
- Bars per phase and edge vs flat orientation: CDA ampacity tables cover these. Values were not retrieved. [UNVERIFIED / Needed]
- AC skin and proximity effects: increase effective resistance and must be included for larger bars and multi-bar phases. Correction factors were not retrieved. [Needed]
- Joint design (overlap, bolt count, torque, plating): not retrieved. [Needed: manufacturer and CDA guidance.]

### 3.3 Aluminum vs copper

Copper conductivity is roughly 60% higher than aluminum. For equal resistance an aluminum bar needs about 1.6× the cross-section. [UNVERIFIED: general knowledge.]

---

## 4. Short-circuit withstand and bracing

### 4.1 Ratings

- Short-time and momentary ratings are defined in C37.20.1 and C37.20.2. Values were not retrieved. [Needed]
- UL 891 covers switchboards up to 200 kA SCCR per the scope snippet. It does not cover switchboards with short-time current ratings. [UNVERIFIED: snippet from https://www.orderline.com/csa-c22-2-no-244-19-national-standard-of-canada-reaffirmed-2024-switchboards]
- Intertek: UL 1558 is listed for higher fault current ratings and short-time withstand than UL 891. The article gives no numbers. [VERIFIED: https://www.intertek.com/blog/2026/07-29-ul-891-vs-ul-1558/]

### 4.2 Electromagnetic force (IEEE 605)

Verified from the EPRI report on IEEE 605 (2012 update, *Reevaluation of IEEE Standard 605's Calculation of Short Circuit Force on Rigid Busbar Structures*). [VERIFIED: https://restservice.epri.com/publicdownload/000000000001024226/0/Product, PDF text extracted locally]

- **Peak asymmetrical current assumption.** IEEE 605 assumes peak asymmetric current = 2 × peak symmetric current (fully offset). [VERIFIED: EPRI §2]
- **Decrement factor.** Corrects for the offset decay. Defined with Ta = (X/R)/(2πf) and Df = a function of Ta and f (IEEE 605-2008 §11.3.3.2). The exact closed form should be copied from the standard, not from this note. [VERIFIED for Ta definition and structure: EPRI eq. 1.7 and 1.8. Exact expression UNVERIFIED because the PDF extraction was garbled.]
- **Corrected force.** F_corrected = Df² × Kf × F_sc. [VERIFIED: EPRI eq. 1.6]
- **Structure flexibility factor Kf.** Kf = 1 for three-phase supports. Single-phase values come from a figure (IEEE 605-2008 Figure 20). [VERIFIED: EPRI §2]
- **Basic force constant.** IEEE 605-1998 uses C = 5.4 × 10⁻⁷ with D = center-to-center spacing in inches and tf = short-circuit duration. [VERIFIED: EPRI eq. 1.9 and text]
- **Span correction factor Γ and the 2008 basic force equation constant** are shown in EPRI Figure 2-1 as an image. Not read. [Needed]

### 4.3 Maximum allowable span

- **IEEE 605-2008:** LS = sqrt( A · J · σ_allow / (F_T · D_o) ), where J is the bending moment of inertia, F_T the total force per unit length, D_o the conductor outside diameter, and A depends on end conditions. [VERIFIED: EPRI eq. 1.12]
- **Table 2-1 A factors (2008):** pinned-pinned or pinned-fixed single span = 16; fixed-fixed = 24. [VERIFIED: EPRI Table 2-1]
- **IEEE 605-1998:** LS = C · sqrt( A · F_A · S / F_T ), with C = 3.16 (metric) or 3.46 (English), and A = 8 (single span pinned-pinned or pinned-fixed), 12 (fixed-fixed), 8 (two-span continuous). [VERIFIED: EPRI eq. 1.13 and Table 2-1]

### 4.4 Accuracy of the static method

- EPRI finds IEEE 605 static analysis "overly conservative" because it ignores dynamic response. [VERIFIED: EPRI abstract]
- Of five hand methods tested against nine experiments, the Attri-Edgar Dynamic Stress Model for Bus Supports predicted forces most accurately. [VERIFIED: EPRI abstract and conclusions]
- The EPRI report includes MATLAB code for Attri-Edgar in its Section 11. [VERIFIED: EPRI §11 index]
- A vendor blog claims the 1998 and 2008 editions define Df differently and that forces at typical X/R are about three times higher. The blog's own math does not support this and its constants were not verified. Do not use it. [UNVERIFIED: https://industrialmonitordirect.com/de/blogs/knowledgebase/ieee-605-short-circuit-force-1998-vs-2008-equation-differences]

### 4.5 Insulator cantilever

IEEE 605 has a cantilever-force section (EPRI §2 "Short Circuit Induced Insulator Cantilever Force"). The formula was not extracted. [Needed]

---

## 5. Clearances, creepage, BIL

- **UL 891 spacings** (through air and over surface, by voltage band): a forum/blog source gives 1 in through air, 2 in over surface, and 1 in to ground for 250–600 V. It cites "Table 24.1", which could not be confirmed. The same source is internally inconsistent on dielectric test values. [UNVERIFIED: https://industrialmonitordirect.com/blogs/knowledgebase/600v-switchgear-bus-bar-spacing-requirements-per-ul-891]
- **UL 508A** feeder values at 600 V (1 in through air, 2 in over surface) are consistent with the above but are a different standard. [UNVERIFIED: vendor documents]
- **UL 891 vs UL 1558** on bus insulation and clearance: Intertek does not address either. Another blog claims UL 1558 requires insulated bus with greater clearances and UL 891 allows bare bus. [UNVERIFIED: secondary blog]
- **C37.20.2 BIL, 15 kV class:** 95 kV BIL, 4.76 kV class 60 kV BIL, per an Eaton product bulletin that cites C37.20.2. [UNVERIFIED: https://eatonarabia.com/wp-content/uploads/2022/01/5-15kv-standard-pa02201001e.pdf, secondary]. Usual 15 kV class values (15.5 kV max, about 36 kV one-minute dry withstand, 95 kV BIL) are general knowledge only. [UNVERIFIED]

---

## 6. Ventilation and heat dissipation

Not researched successfully in this session. Proposed method for implementation (general engineering practice, to be validated against the standards and manufacturer data):

1. Bus loss per phase: P_bus = I²·R_ac · L, with R_ac from the bar resistance at operating temperature, multiplied by skin and proximity factors.
2. Breaker loss: from manufacturer data at rated current (not from the standard).
3. Enclosure heat balance: P_total = P_bus + P_breaker + P_other. Required ventilation or heat rejection: Q = P_total − h·A·ΔT, with h and A from the enclosure geometry and ventilation.

[UNVERIFIED: general engineering method. Need IEEE C37.23 loss annex and the manufacturer's breaker loss data.]

---

## 7. Proposed implementation algorithm (structure only, parameters pending standards)

Inputs: product family (UL 891 / UL 1558 / C37.20.2 / C37.23), rated voltage, continuous current, SCCR or short-time rating, bus material, ambient, bus arrangement, bar spacing, support spacing, X/R, fault duration.

1. **Select standard and limits.** Look up temperature-rise limits, spacings, and BIL for the family. [Values pending]
2. **Continuous current sizing.** Choose bar cross-section and number per phase so the CDA ampacity at the design rise (target ≤30 °C, cap per standard) is ≥ rated current. Correct for orientation, bar count, skin and proximity effects, and enclosure derating. [Method only]
3. **Joint check.** Joint area, bolt count, torque, and plating per the manufacturer's standard practice.
4. **Thermal check.** Estimate losses (Section 6), compute steady-state rise, compare to the limit from Step 1. Iterate Step 2 if it fails.
5. **Peak fault force.**
   - Ta = (X/R) / (2πf)
   - Df from the IEEE 605-2008 §11.3.3.2 closed form [copy from standard]
   - Basic force from IEEE 605 (use the edition the product is tested to)
   - F_corrected = Df² · Kf · F_sc (Kf = 1 for three-phase supports)
6. **Span.** LS = sqrt(A·J·σ_allow / (F_T·D_o)), with A from Table 2-1 [16 or 24 for 2008]. Check LS against the actual support spacing.
7. **Support and insulator cantilever check.** Use the IEEE 605 cantilever formula and insulator rating. If the static result is too conservative, consider the Attri-Edgar method, which EPRI found more accurate.
8. **Clearances.** Check through-air and over-surface spacings for the voltage band and BIL from Step 1.
9. **Output.** Bar count and size, rise estimate, support span, insulator rating, clearances, and a pass/fail list. Flag any "UNVERIFIED" constant as an input the user must confirm.

---

## Sources

Verified (read in this session):
- EPRI, *Reevaluation of IEEE Standard 605's Calculation of Short Circuit Force on Rigid Busbar Structures* (2012): https://restservice.epri.com/publicdownload/000000000001024226/0/Product
- Intertek, UL 891 vs UL 1558 comparison (2026): https://www.intertek.com/blog/2026/07-29-ul-891-vs-ul-1558/

Search snippets and secondary (unverified):
- ANSI webstore, CSA C22.2 No. 244 listing: https://webstore.ansi.org/standards/csa/csac2224419r2024
- Orderline, CSA C22.2 No. 244 listing: https://www.orderline.com/csa-c22-2-no-244-19-national-standard-of-canada-reaffirmed-2024-switchboards
- CSA Group, CSA C22.2 No. 244 product page: https://www.csagroup.org/fr/store/product/2426063/
- ANSI webstore, IEEE C37.20.2 listing: https://webstore.ansi.org/standards/ieee/ieeec37201999r2005
- IEEE SA, C37.23 listing: https://standards.ieee.org/ieee/C37.23/5577
- IEEE PES Switchgear minutes (C37.23 scope): https://ewh.ieee.org/soc/pes/switchgear/minutes/2012-1/S12SAa5.pdf
- Eaton, 5-15 kV standard bulletin (BIL): https://eatonarabia.com/wp-content/uploads/2022/01/5-15kv-standard-pa02201001e.pdf
- Schneider Electric blog, IEC 61439 rated current: https://blog.se.com/infrastructure-and-grid/power-management-metering-monitoring-power-quality/2018/05/23/iec-61439-rated-current-of-electrical-panel-and-switchboard-protection-devices
- Mike Holt forums (NEC 366.23 quote, bus ampacity, UL 489 breaker terminals, NEC 310.15 marking): https://forums.mikeholt.com/threads/bus-bar-ampacity.30005/latest and https://forums.mikeholt.com/goto/post?id=2675540
- Industrial Monitor Direct blogs (UL 891 spacing, IEEE 605 1998 vs 2008): https://industrialmonitordirect.com/blogs/knowledgebase/600v-switchgear-bus-bar-spacing-requirements-per-ul-891 and https://industrialmonitordirect.com/de/blogs/knowledgebase/ieee-605-short-circuit-force-1998-vs-2008-equation-differences
- CDA busbar ampacity table page (search snippet; fetch returned 403): https://copper.org/applications/electrical/busbar/bus_table3.php

Blocked during this session (not read):
- copper.org design guide PDF (HTTP 403)
- NEMA PB 2 (not found)
- UL Standards (UL 891, UL 1558, UL 67, UL 857), IEEE C37.20.1/.2/.3/.7, C37.23 full text, CSA C22.2 No. 31 and No. 29, IEEE 605-2008 full text

---

## Open questions / needs checking

1. **UL 891 temperature-rise table.** Confirm the 65 °C (silver-plated) and 50 °C (unplated) values, the test ambient, and the stabilization criterion. The 50 °C value may be the UL 489 breaker-terminal limit, not a UL 891 bus limit.
2. **C37.20.1 and C37.20.2 temperature rise** for bus and connections.
3. **Current density.** Confirm the NEC 366.23 values (1000 A/in² copper, 700 A/in² aluminum; the request's 750 A/in² aluminum figure is not supported).
4. **CDA ampacity tables** at 30/50/65 °C rise: bars per phase, edge vs flat, skin and proximity factors, joint and plating guidance. Need the full CDA guide, which the site blocked.
5. **IEEE 605-2008 closed forms** for Df, the basic force equation (with Γ), and the cantilever formula. The EPRI extraction did not render the equations cleanly. Read the standard.
6. **Short-time and momentary ratings** in C37.20.1 and C37.20.2, and the UL 891 SCCR basis.
7. **UL 891 spacing table** (Table 24.1 is unconfirmed; the blog's figures are internally inconsistent).
8. **UL 1558 vs CSA C22.2 No. 31** harmonization status.
9. **C37.20.2 voltage and BIL table** (15 kV class: confirm 95 kV BIL and the 36 kV dry withstand).
10. **Losses and breaker loss data** for the heat balance (IEEE C37.23 loss annex; breaker manufacturer data).
11. **CSA scopes** for C22.2 No. 29, No. 214, and No. 31.
12. **Re-run the search** in a later session, when rate limits are clear, targeting copper.org PDFs, UL Standards previews, and IEEE SA abstracts for C37.20.x and C37.23.
