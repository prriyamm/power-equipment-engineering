# Cable Bus Design Research (US / Canada)

**Scope:** NEC (NFPA 70) Article 370 and related articles; CEC (CSA C22.1) cablebus rules; CSA/ANSI C22.2 No. 273 (cablebus product standard); IEEE and UL context; manufacturers; design algorithm.
**Status as of 2026-10-10:** Partial. Primary code text (NEC 370 clause-level, CEC rules, CSA C22.2 No. 273 body) could not be read from accessible sources. Most clause-level content below is **[UNVERIFIED]** and must be checked against the official text before use in any calculation or product document.

**Tag key**
- `[VERIFIED: URL]`: read in a fetched page or a search-result snippet from that URL.
- `[UNVERIFIED]`: from general engineering knowledge or a secondary/forum source; needs checking against the primary document.

---

## 0. Summary of what was and was not verified

| Item | Status |
|---|---|
| CSA/ANSI C22.2 No. 273:19 is the current cablebus product standard; scope and definition | VERIFIED (snippet) |
| CSA C22.2 No. 273 has an "allowable ampacity" section (CE Code and NEC methods, temperature rise, correction factors) and a phase-arrangement section | VERIFIED (table of contents only) |
| Nameplate content (ampacity at stated ambient/temp, short-circuit rating, 75 C minimum ampacity) | VERIFIED (IAEI 2013 article; edition may have changed since) |
| NEC 370 section numbers and text (370.1 to 370.80) | UNVERIFIED: could not read the code text |
| NEC 370.80 uses free-air ampacity from 310.15(B)(17) with spacers on factory cable tray | VERIFIED only through forum posts; treat as a lead |
| 110.14(C)(1) interaction with 370.80 (termination temperature) | Disputed in forums; needs AHJ and listing confirmation |
| 2023 vs 2026 changes to Article 370 | Partly verified (2023 simplification and fire-stop alignment via secondary summary); 2026 renumbering to Chapter 9 "922" is a forum-table reading, **unconfirmed** |
| Medium-voltage cablebus (Article 311 / 315 / 370 scope above 1000 V) | Not resolved; Article 311 moved to Article 315 in 2023 (verified via secondary source); cablebus MV scope UNVERIFIED |
| Short-circuit bracing formula (IEEE 605) | Not verified; the only source is a blog with internal inconsistencies |
| MP Husky cablebus data | Partial: 100 kA RMS bracing claim (catalog listing, UNVERIFIED against datasheet) |
| Superior Tray, Pow-R-Way, Cablebus Systems Corp, Powell, Salient, Calvert | Not found in search; no data |
| UL standard for cablebus ampacity testing | Not identified; UL 857 is the busway standard, not cablebus |

---

## 1. NEC Article 370 (Cablebus)

### 1.1 Structure and numbering
- Cablebus has historically been in NEC **Article 370**. [UNVERIFIED for 2023 and 2026 numbering; see section 1.4]
- One 2023 training summary says flexible bus systems were moved to a new **Article 371** and that cablebus stays in Article 370. [VERIFIED: https://www.vectorsolutions.com/courses/or-2023-nec-changes-wiring-methods-and-general-use-equipment-pgm/ (snippet)] Another source describes Article 370 as "Auxiliary Gutters", which conflicts. Treat that as a search-result error, but confirm.
- ECM's 2023 coverage discusses flexible bus under a "370.18" heading, which seems to conflict with the Article 371 split. [VERIFIED: https://www.ecmag.com/section/codes-standards/continuing-our-code-journey-accepting-nec-change-part-10 (snippet)] Check directly.

### 1.2 Section-by-section (UNVERIFIED from memory; must be checked against the official NEC text)

| Section (approx.) | Topic | Status |
|---|---|---|
| 370.1 | Scope: cablebus assemblies of insulated conductors in an enclosed housing | UNVERIFIED |
| 370.2 | Definitions (cablebus, cablebus enclosure, etc.) | UNVERIFIED |
| 370.10 | Uses permitted (including wet / damp locations in recent cycles) | UNVERIFIED. The 2023 change note says cablebus is now permitted in wet locations, and the curb requirement at floor penetrations was removed. [VERIFIED (secondary, snippet): https://www.ecmag.com/section/codes-standards/continuing-our-code-journey-accepting-nec-change-part-10] |
| 370.12 | Uses not permitted | UNVERIFIED |
| 370.18 | Installation (2023: simplified; fire-stop requirements aligned with cable tray) | Partly VERIFIED (secondary summary; see section 1.4) |
| 370.20 | Conductors: size and minimum size | Secondary quiz source gives minimum **1/0 AWG** and "sized in accordance with the design of the cablebus". [VERIFIED (secondary): https://www.ecmweb.com/code-quiz-day/cablebus-conductor-sizing (not fetched, snippet only)] Confirm against 2023/2026 text; may be from an earlier edition. |
| 370.23 | Support of conductors and support spacing / blocks | UNVERIFIED |
| 370.30 / 370.40 | Enclosure, ventilation, enclosure fill | UNVERIFIED |
| 370.60 | Grounding and bonding (enclosure as equipment grounding conductor) | UNVERIFIED |
| 370.80 | Ampacity: free-air ampacity from 310.15(B)(17) for conductors on factory cable tray with spacers | Forum-sourced; see 1.3 |
| 370.120 | Marking (2023 revised; nameplates at terminating ends and a second marking requirement) | Partly VERIFIED (secondary) |

### 1.3 Ampacity provisions (370.80) and related rules

- **Free-air basis.** A forum poster quotes 370.80 as allowing free-air ampacities of 310.15(B)(17) for a cablebus feeder with conductors held apart by spacers on factory cable tray. [VERIFIED (forum, not authoritative): https://forums.mikeholt.com/threads/110-14-c-1-vs-370-80-cablebus-ampacity-at-swbd-terminations.140161/latest (snippet)] **Mike Holt forum fetch returned HTTP 403; this is a search-snippet verification only.**
- **Column choice.** Forum posters say the 75 C column is the minimum for switchgear terminations. Some say the 90 C column may be used only if the cablebus and termination boxes are rated for 90 C. [VERIFIED (forum): same thread, snippet] [UNVERIFIED as code interpretation]
- **Termination limit (110.14(C)(1)).** One poster states that 110.14(C)(1) says conductor ampacity should be based on the 310.15(B)(16) raceway columns unless the equipment is listed and marked otherwise. Practitioners disagree on how this interacts with 370.80. **Unresolved. Confirm with the AHJ and the cablebus listing.**
- **Cablebus nameplate ampacity.** The IAEI 2013 article says nameplate ampacity is tied to a stated ambient and maximum operating temperature, with a minimum allowable ampacity based on 75 C. It does not discuss 370.80 or free-air derating. [VERIFIED: https://iaeimagazine.org/magazine/features/cablebus (fetched; 2013 edition)]

### 1.4 2023 vs 2026 changes

**2023 (secondary sources):**
- Installation requirements simplified in 370.18. [VERIFIED (secondary, snippet): https://www.ecmag.com/section/codes-standards/continuing-our-code-journey-accepting-nec-change-part-10]
- Fire-stop requirements now align with cable tray. [VERIFIED (secondary, snippet): same]
- Floor-penetration curb requirement removed; cablebus allowed in wet locations. [VERIFIED (secondary, snippet): same]
- Marking revised in 370.120. [VERIFIED (secondary, snippet): same]

**2026 (unconfirmed):**
- A Mike Holt forum thread shows a 2026 reorganization table that appears to move cablebus into Chapter 9 as **922 Cablebus 370**. The layout is hard to read; this may be a misreading. [VERIFIED (forum table, unclear): https://forums.mikeholt.com/threads/2026-nec-reorganization.2580187/post-2910670 (snippet)] **UNCONFIRMED. Check the NFPA 2026 NEC text and the NFPA Public Comment / First Revision list.**

### 1.5 Article 311 / medium voltage

- **Article 311 was moved to Article 315** ("Medium Voltage Conductors, Cable, Cable Joints, and Cable Terminations") in the 2023 NEC. Article 315 also adds MV cable joint, connector and termination requirements. [VERIFIED (secondary): https://iaeimagazine.org/columns/nfpa-code-talk/stepping-up-medium-voltage-requirements-in-the-nec/ (snippet)]
- Medium voltage in the 2023 NEC starts above 1000 V ac, 1500 V dc nominal. [VERIFIED (secondary): same]
- General wiring methods for systems over 1000 V: **Article 305**. [VERIFIED (secondary): same]
- **Whether Article 370 (cablebus) applies to medium-voltage cablebus, and which provisions apply above 1000 V, is UNVERIFIED.** Cablebus product standards cover up to 46 kV (see section 2). The NEC scope needs checking.

---

## 2. CEC (CSA C22.1) and CSA product standard

### 2.1 Canadian Electrical Code
- The IAEI 2013 article cites **CE Code Part I Rule 12-2252 (use of cablebus)**, **12-2260**, and **8-104**. [VERIFIED (2013 article): https://iaeimagazine.org/magazine/features/cablebus]
- Rule 12-2252 also defines **Class A** (protection from contact by enclosure design) and **Class B** (accessible only to authorized persons, isolated by elevation or barriers, serviced by qualified personnel). [VERIFIED (2013 article)]
- **Current CEC edition numbering and text: UNVERIFIED.** The CEC is revised on a cycle; confirm the clause numbers in the current edition.
- The user's note suggested "Section 12, rules around 12-2250 onward". Rule 12-2252 is confirmed from the 2013 source. The "Section 12" and "12-2260" references are partly verified through the same source; current numbering is unknown.

### 2.2 CSA/ANSI C22.2 No. 273:19 Cablebus
- **Current edition:** CSA/ANSI C22.2 No. 273:19, Cablebus, Nov 2019; supersedes C22.2 No. 273-14. Reaffirmed (R2024) per one listing. [VERIFIED: https://scc-ccn.ca/standardsdb/standards/4030085 ; https://www.csagroup.org/store/product/2427080/ ; https://www.standards.nimonik.com/products/csa/c22pt2-no-273/ (snippets)]
- **Scope:** complete cablebus systems, termination to termination, with fittings; rated up to **46 kV ac or dc**. Intended for use with NEC, CEC Part I and CSA C22.2 No. 0. [VERIFIED: https://scc-ccn.ca/standardsdb/standards/4030085 (snippet, clause 1.1)]
- **Busway exclusion:** metal-enclosed busways are covered by **CSA C22.2 No. 201** and **CSA C22.2 No. 27 / UL 857**, not by No. 273. [VERIFIED (snippet, clause 1.1)]
- **Definition:** an assembly of single conductors and/or cables carrying large currents and withstanding short-circuit, loading and bonding effects, in a completely enclosed, ventilated or non-ventilated metal housing. [VERIFIED (snippet, clause 1.2)]
- **Transition enclosures** between cablebus and adjoining equipment are covered (2019 edition). [VERIFIED (snippet, clause 1.3)]
- **Units:** SI units of record. [VERIFIED (snippet, clause 1.4)]
- **Table of contents includes:** "Allowable ampacity ratings" (CE Code method, NEC method, temperature rise with and without specific distribution equipment, correction factors); "4.13 Conductor phase arrangement"; an informative annex with test guidelines for cables in cablebus. [VERIFIED: TOC snippet from https://store.accuristech.com/api/products/preview/2096216 and https://www.csagroup.org/store/product/2427080/]
- **Nameplate (2013 article, pre-2019 edition):** manufacturer, month/year of manufacture, design drawing number, nominal voltage, frequency, phases, 3- or 4-wire, short-circuit rating, allowable ampacity at stated ambient and max operating temperature, 100% and 80% continuous-rated OCPD ratings, minimum ampacity at 75 C, number and size of conductors per phase, enclosure material, "do not use as walkway, ladder or support" warning. [VERIFIED (2013 article); confirm against 2019 edition]
- **Clause text (ampacity methods, spacing, phase arrangement, bracing, test procedures): NOT READ. Must be purchased from CSA Group or obtained from a library.** [UNVERIFIED]

### 2.3 UL
- UL 857 is the busway standard (see 2.2). It is not the cablebus standard. [VERIFIED (snippet, 2.2)]
- A forum post says cablebus ampacity is what was tested during UL recognition, and that published ratings mean little without the final assembly and applicable UL standard. Informal source. [VERIFIED (forum, snippet)]
- **The specific UL standard for US cablebus ampacity testing: NOT IDENTIFIED.** Check the UL product directory for the listed cablebus products. [UNVERIFIED]

### 2.4 IEEE
- Relevant IEEE references to confirm (none read): IEEE C37.23 (metal-enclosed bus) [UNVERIFIED as applicability to cablebus]; IEEE 605 (bus design: short-circuit forces, support spacing) [UNVERIFIED]; IEEE 835 (power cable ampacity) [UNVERIFIED]; IEEE 738 (conductor temperature) [UNVERIFIED]. IEEE Switchgear Committee presentation on cable bus (2021) exists but the PDF returned as binary. [VERIFIED: https://r7.ieee.org/sas-pesias/wp-content/uploads/sites/47/2021/02/IEEE-Cable-Bus-Presentation-Feb-23-2021-Reduced.pdf (exists; content not read)]
- IEEE 605 short-circuit force: a blog reports that the 2008 edition's short-circuit force equation (decrement factor squared, span correction factor Gamma) gives forces about **2.8 to 3.1 times** the 1998 result at X/R 10 to 30. **Source is a secondary blog with internal arithmetic inconsistencies; do not use without checking IEEE 605-2008 Table 11 and Table 14 directly.** [VERIFIED (secondary): https://industrialmonitordirect.com/zh-hans/blogs/knowledgebase/ieee-605-short-circuit-force-1998-vs-2008-equation-differences (snippet)]

---

## 3. How cablebus ampacity is engineered

All items **UNVERIFIED** unless noted.

### 3.1 Free-air basis and spacing
- Cablebus conductors are ventilated and spaced, so the free-air ampacity of Table 310.15(B)(17) is the starting basis, provided spacing is maintained. [VERIFIED (forum lead): mike holt threads, snippet only]
- Forum consensus: spacing is maintained with spacer blocks or tray; one engineer proposed spacing of "100%+" around cables to use the single-conductor free-air rating. Treat as a practitioner rule, not code text. [VERIFIED (forum, snippet)]
- One forum post cites NEC 392.80 for triangular or square arrangements of single conductors with maintained free airspace, figure about **2.15 x conductor diameter**. **Not confirmed against code text.** [UNVERIFIED]
- A common practice in published cablebus material is one-conductor-diameter spacing between cables. [UNVERIFIED]
- Patent literature says allowable spacing and orientation depend on current, cable size, and insulation thickness/quality, and is set per installation. [VERIFIED (patent snippets): https://patents.google.com/patent/US8558112 ; https://patents.google.com/patent/US9059575]

### 3.2 Thermal method and derating (general engineering; UNVERIFIED specifics)
- Two methods appear in CSA C22.2 No. 273 (CE Code and NEC allowable ampacity; temperature rise with and without distribution equipment) and correction factors. [VERIFIED: TOC snippet]
- Neher-McGrath (1957) and IEEE 835 are the usual thermal approaches for cable ampacity; CYMCAP implements Neher-McGrath and IEC 60287. [UNVERIFIED for this use; the CYME reference is from the workspace research note]
- Derating factors to include in a model (UNVERIFIED as code values): ambient temperature; number of conductors per cablebus; enclosure type (ventilated vs non-ventilated); solar gain on outdoor runs; vertical vs horizontal orientation (chimney effect on ventilated enclosures); enclosure covers; grouping with other cablebus or cable tray.
- **Solar and enclosure correction values: not found. Get them from the CSA standard annex or the manufacturer.**

### 3.3 Termination limits
- Forum consensus: for switchgear or LV terminations, use **75 C** ampacity; 90 C only where the termination and enclosure are listed for 90 C. [VERIFIED (forum): snippet] [UNVERIFIED as code]
- See the 110.14(C)(1) dispute in section 1.3.

### 3.4 Phase arrangement and balance
- Forum recommendation for a single layer: interleaved **A-B-C-A-B-C** rather than grouped **A-A-A-B-B-B**. [VERIFIED (forum): snippet]
- For closely packed (multi-layer) cablebus: a poster suggests **ABCCBA** mirrored in each layer, and says the supplier's phasing gave lowest reactance and best current balance. [VERIFIED (forum): snippet]
- CSA C22.2 No. 273 has a "Conductor phase arrangement" section (4.13). [VERIFIED: TOC snippet]
- Phase arrangement affects circulating current and losses. A JICABLE 2023 paper finds that circulating-current losses depend strongly on phase orientation. **That paper is about buried metallic-sheathed cables;** it applies only in part to cablebus. [VERIFIED: https://www.jicable.org/TOUT_JICABLE_FIRST_PAGE/2023/2023-B4-3_page1.pdf (snippet)]

---

## 4. Induced currents and losses

Mostly **UNVERIFIED**. The sources read did not give formulas for enclosure losses or eddy-current heating.

- **Parallel conductors and unequal sharing.** Current in parallel conductors divides by impedance. Unequal reactance from position (inner vs outer conductors, different distances to the enclosure) causes unequal current. Balancing requires transposition or a symmetrical arrangement. [UNVERIFIED: general principle]
- **Magnetic force between conductors.** Conductors carrying current in the same direction attract; opposite directions repel. Force per unit length between two parallel conductors (SI): F/L = 2 x 10^-7 x I1 x I2 / d (N/m), with I in amperes and d in metres. For peak fault current use the peak values. [UNVERIFIED: classical formula; confirm against IEEE 605 and CSA 273]
- **Eddy currents in aluminum or steel enclosures.** Ferromagnetic enclosures (galvanized carbon steel) heat more than non-magnetic enclosures (aluminum, stainless steel). Aluminum enclosures reduce magnetic heating but can have circulating eddy-current losses. Enclosure material is on the nameplate; the choice affects losses and temperature rise. [UNVERIFIED]
- **Phasing and enclosure heating.** Phase arrangement changes the external field and eddy losses in the enclosure. Quantify with FEA (Ansys Maxwell, COMSOL, FEMM) or a validated vendor method. [UNVERIFIED]
- **MP Husky claims 90% of its CSA cablebus systems use 6063-T6 aluminum, with stainless and galvanized steel available.** [VERIFIED (catalog listing): https://archiexpo.com/prod/mp-husky/product-149710-1666528.html (snippet)]

---

## 5. Short-circuit bracing, support blocks, enclosure as grounding conductor

### 5.1 Bracing
- **MP Husky** states support blocks provide "minimum 100 kA RMS symmetrical" short-circuit bracing. [VERIFIED (catalog listing, snippet): https://pdf.archiexpo.com/pdf/mp-husky/cable-bus/149710-264272.html ] **Confirm against the datasheet or test report.**
- MP Husky's literature notes that cablebus was tested on a **600 V, 3-phase** system, with the test details cut off. [VERIFIED (snippet)]
- The short-circuit rating is on the nameplate; the IAEI 2013 article gives no bracing method or value. [VERIFIED (2013 article)]

### 5.2 Force per unit length and support spacing
- Peak force between parallel conductors during a fault: classical form F/L = 2 x 10^-7 x i_peak^2 / d (N/m) [UNVERIFIED]. Asymmetrical (offset) peak currents use i_peak = sqrt(2) x kappa x I_sym, with kappa the peak factor from X/R. [UNVERIFIED]
- Support-block bracing must resist the peak force for the calculated span. IEEE 605 provides the bus-specific method, including span correction factors. A 2008-edition variant gives substantially higher forces at high X/R (see section 2.4). [UNVERIFIED: must read IEEE 605-2008]
- **Do not design bracing from the blog formula. Use IEEE 605-2008 and the manufacturer's test data.**

### 5.3 Enclosure as equipment grounding conductor
- The NEC grounding and bonding requirements for cablebus are in 370.60 (section numbering UNVERIFIED). Enclosure bonding is typically required; confirm the code text and the listing. [UNVERIFIED]
- IAEI article: shield bonding and shield grounding "where applicable"; enclosure material and bonding are set out in the manufacturer's drawings. [VERIFIED (2013 article)]

### 5.4 Fault current ratings
- Nameplate short-circuit rating required (IAEI 2013, and CSA 273 nameplate rules). [VERIFIED]
- MP Husky: available short-circuit current equals the utility or generator current through the transformers; large motor contribution must be included. [VERIFIED (snippet)]

---

## 6. Manufacturers

| Manufacturer | Status | Data found |
|---|---|---|
| **MP Husky** | Found | Stainless and galvanized steel, 6063-T6 aluminum (90% of CSA cablebus). 100 kA RMS bracing claim (catalog). 600 V, 3-phase test reference. Ampacity tables **not found**. [VERIFIED: archiexpo listings] |
| **Superior Tray Systems** | Not found | None |
| **Pow-R-Way** | Not found | None |
| **Cablebus Systems Corp** | Not found | None |
| **Powell** | Not found | None |
| **Salient Systems** | Not found | None |
| **Calvert / Eaton** | Not found; the user's "Calvert/Eaton?" was a question. No evidence found that Calvert makes cablebus. | None. Check before listing. |

Typical rating ranges (600 V to 35 kV, 400 to 6000 A) were given in the request, **not verified**. CSA 273 scope covers up to 46 kV. [VERIFIED for 46 kV; the rest UNVERIFIED]

**Test standards cited:** CSA/ANSI C22.2 No. 273 (cablebus); CSA C22.2 No. 201 and C22.2 No. 27 / UL 857 (busway, excluded from No. 273); IEEE C37.23 and IEEE 605 (bus, UNVERIFIED as applicable). [VERIFIED (scope); others UNVERIFIED]

**Next step for vendor data:** request from each manufacturer (a) ampacity tables by conductor size, number per phase and enclosure type, (b) test reports for short-circuit bracing and temperature rise, (c) listing reference (UL file number or CSA certificate), (d) phasing recommendation.

---

## 7. Design algorithm (for implementation)

This is a structure for a calculation tool. Every step that depends on a code value must be filled from the standard text before implementation. Tag each step with its source.

### 7.1 Inputs
- System: nominal voltage (V), phases (3 or 3+N), frequency (60 Hz; 50 Hz not applicable in US/Canada market), fault current at bus (kA sym), X/R at point, fault clearing time (s).
- Load: design current (A), continuous/non-continuous, 80% vs 100% overcurrent-device rule (per nameplate).
- Route: length (m or ft), vertical rise, horizontal/vertical orientation, indoor/outdoor, solar exposure, ambient (C), ventilation.
- Conductor: material (Cu/Al), insulation type and rating (75 C / 90 C), number of conductors per phase (initial guess).
- Enclosure: material (aluminum / galvanized steel / stainless), ventilated or not, class A or B (CE rule 12-2252 per 2013 source).
- Terminations: device rating (75 C or 90 C), listing.
- Standards: NEC edition (2023 or 2026), CEC edition, CSA 273 edition.

### 7.2 Steps
1. **Minimum conductor size.** Apply the 1/0 AWG minimum (370.20, UNVERIFIED) and size from the design current using the chosen ampacity basis.
2. **Ampacity basis.** Select either the NEC 370.80 free-air method (310.15(B)(17) with 75 C termination limit) or the CSA 273 allowable-ampacity method (CE Code or NEC method, or temperature-rise method). Record which one. [UNVERIFIED method details]
3. **Apply derating.** Ambient, number of conductors, enclosure type, solar, orientation, grouping. Use values from the code or the CSA annex. [UNVERIFIED values]
4. **Number of conductors per phase.** Choose N so that derated ampacity per phase >= design current / (balance factor). Start N = 1 and increase.
5. **Arrangement.** Use interleaved or ABCCBA per supplier recommendation; check reactance balance (compute each conductor's loop impedance for sharing; see section 4). [UNVERIFIED]
6. **Enclosure size.** Use spacing rule (conductor diameter x factor; 2.15 D for NEC 392.80 triangular/square arrangement is UNVERIFIED) plus support and bending space; select the enclosure size from the manufacturer or the CSA dimensional tables.
7. **Voltage drop.** For each phase: Z = R + jX per unit length from conductor data and arrangement; drop = sqrt(3) x I x (R cos phi + X sin phi) x L. Use the actual phase-sharing impedances. [UNVERIFIED formula choice: confirm against the standard practice in the user's firm]
8. **Losses.** Conductor I^2 R losses per phase; enclosure eddy and hysteresis losses (from FEA or vendor); sum for thermal design.
9. **Temperature rise.** Solve the thermal model (conductor, insulation, air inside enclosure, enclosure surface, ambient). Check against 75 C / 90 C limits. Neher-McGrath or IEEE 835 approach. [UNVERIFIED]
10. **Short-circuit bracing.** Compute peak force per unit length (F/L = 2 x 10^-7 x i_peak^2 / d, with i_peak from X/R and clearing time) and select support-block spacing so that the block's rated bracing exceeds the force. Use IEEE 605-2008 for bus-specific factors. [UNVERIFIED]
11. **Fault withstand.** Check conductor thermal limit (I^2 t) and enclosure short-circuit rating; compare to the nameplate rating.
12. **Grounding.** Enclosure bonding and continuity per NEC 370.60 (UNVERIFIED section) and CEC rules.
13. **Fire stopping, wet location, transition enclosures.** Per 2023 and 2026 NEC changes (secondary sources) and CSA 273 transition-enclosure rules.
14. **Output.** Conductor size, number per phase, arrangement, enclosure size, derated ampacity, voltage drop, losses, temperature rise, bracing spacing, fault rating, listing references, and the code references used for each line.

### 7.3 Open decisions for the implementer
- Which ampacity method is the firm's default (NEC 370.80 or CSA 273)?
- Whether to compute sharing and reactance with FEA or a closed-form approximation.
- Whether MV cablebus (above 1000 V) is in scope.

---

## 8. Sources

**Verified (fetched or snippet-read):**
- IAEI Magazine, "Cablebus" (Jan/Feb 2013): https://iaeimagazine.org/magazine/features/cablebus (fetched)
- IEEE Switchgear Committee, "Cable Bus Presentation" (Feb 2021): https://r7.ieee.org/sas-pesias/wp-content/uploads/sites/47/2021/02/IEEE-Cable-Bus-Presentation-Feb-23-2021-Reduced.pdf (exists; binary, content not read)
- CSA/ANSI C22.2 No. 273:19 Cablebus (SCC listing): https://scc-ccn.ca/standardsdb/standards/4030085
- CSA Group product page: https://www.csagroup.org/store/product/2427080/
- CSA standard TOC (Accuristech): https://store.accuristech.com/api/products/preview/2096216
- Nimonik listing (R2024): https://www.standards.nimonik.com/products/csa/c22pt2-no-273/
- SCC notice of intent for cablebus: https://scc-ccn.ca/standards/notices-of-intent/csa-group/cablebus
- MP Husky catalog (ArchiExpo): https://archiexpo.com/prod/mp-husky/product-149710-1666528.html ; https://pdf.archiexpo.com/pdf/mp-husky/cable-bus/149710-264272.html
- ECM "Continuing our code journey, part 10": https://www.ecmag.com/section/codes-standards/continuing-our-code-journey-accepting-nec-change-part-10 (snippet)
- Vector Solutions 2023 NEC changes (Article 371 flexible bus): https://www.vectorsolutions.com/courses/or-2023-nec-changes-wiring-methods-and-general-use-equipment-pgm/ (snippet)
- IAEI, "Stepping Up Medium Voltage Requirements in the NEC": https://iaeimagazine.org/columns/nfpa-code-talk/stepping-up-medium-voltage-requirements-in-the-nec/ (snippet)
- ECMWEB code quiz (cablebus conductor sizing): https://www.ecmweb.com/code-quiz-day/cablebus-conductor-sizing (snippet)
- Mike Holt Forums (search snippets only; the thread fetch returned 403): https://forums.mikeholt.com/threads/110-14-c-1-vs-370-80-cablebus-ampacity-at-swbd-terminations.140161/latest ; https://forums.mikeholt.com/threads/2026-nec-reorganization.2580187/post-2910670 ; https://forums.mikeholt.com/threads/cablebus-370-4-b-ampacity-limitations.116180/post-116180 ; https://forums.mikeholt.com/threads/cable-bus-conductor-ampacity.149772/latest
- JICABLE 2023 B4-3 (phase orientation, buried cables): https://www.jicable.org/TOUT_JICABLE_FIRST_PAGE/2023/2023-B4-3_page1.pdf (snippet)
- Patents (spacing principle): https://patents.google.com/patent/US8558112 ; https://patents.google.com/patent/US9059575 (snippets)
- IEEE 605 blog (secondary; not authoritative): https://industrialmonitordirect.com/zh-hans/blogs/knowledgebase/ieee-605-short-circuit-force-1998-vs-2008-equation-differences (snippet)

**Not reachable or not read (needed):**
- NFPA NEC 2023 and 2026 Article 370 (and Article 315 / 922 location): https://www.nfpa.org/ (free-access viewer) : NOT READ
- CSA C22.2 No. 273:19 full text: purchase required; NOT READ
- CEC Part I, current edition, Section 12 rule text: NOT READ
- IEEE 605-2008, IEEE 835, IEEE C37.23: NOT READ
- UL cablebus listing directory: NOT READ

---

## 9. Open questions / needs checking

1. **NEC 370 section text (370.1 through 370.120).** Read the NFPA 2023 and 2026 texts. Confirm scope, uses, conductor minimum, support spacing, grounding, and 370.80.
2. **2026 numbering.** Confirm whether cablebus moved to Chapter 9 as 922 and whether section numbers changed.
3. **370.80 vs 110.14(C)(1).** Which termination temperature governs cablebus feeders to switchgear? Ask the AHJ and check the listing.
4. **Medium voltage.** Does Article 370 apply above 1000 V? Does Article 315 apply to any cablebus conductor? Get the MV scope in writing from the code.
5. **CEC rule numbers.** Confirm current Section 12 numbering (12-2252 and 12-2260 from the 2013 article; current edition unknown).
6. **CSA C22.2 No. 273:19 clauses.** Purchase the standard. Check 4.13 (phase arrangement), the allowable-ampacity methods, correction factors, annex test guidelines, and nameplate content.
7. **Spacing rule.** Confirm the spacing used for free-air ratings (one diameter, 2.15 D from NEC 392.80, or CSA-specific). This is central to ampacity.
8. **Solar and enclosure correction factors.** Get the values from the code or CSA annex, or from the vendor.
9. **Short-circuit bracing.** Read IEEE 605-2008 and verify the blog's factors (Gamma, decrement factor, Table 14 50/60 Hz error). Confirm MP Husky's 100 kA claim against the test report.
10. **Enclosure eddy-current and induced losses.** No formulas found. Decide whether to use FEA (Ansys Maxwell, Simcenter MAGNET, COMSOL, FEMM) or a vendor method.
11. **Manufacturers.** Find data for Superior Tray Systems, Pow-R-Way, Cablebus Systems Corp, Powell, Salient Systems. Check whether Calvert makes cablebus at all; the "Calvert/Eaton?" entry may be wrong.
12. **Voltage and current ranges.** The 600 V to 35 kV and 400 to 6000 A ranges in the brief are not verified. CSA 273 covers up to 46 kV.
13. **UL listing.** Identify the UL standard and file for US cablebus listings.
14. **Forum posts.** The Mike Holt threads (403 on fetch) are only search-snippet sources. Do not cite them as code authority.
15. **Article 370 scope conflict.** One source says Article 370 is "Auxiliary Gutters". Confirm the cablebus article number before any document cites it.
