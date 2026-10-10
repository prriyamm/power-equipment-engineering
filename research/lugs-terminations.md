# Cable Lugs and Terminations: Selection Research (US / Canada)

Scope: lug type, size, quantity per terminal, and how terminations are engineered into switchgear, transformer and cable bus. Standards focus: NEC (NFPA 70), CEC Part I (CSA C22.1), UL, CSA, NEMA, IEEE/ANSI. IEC mentioned only for comparison.

Status: **Research draft.** The standards texts themselves (UL 486A-B, UL 486E, NEMA CC 1, NEC 312.6 and 110.14, CEC Rule 4-006 and Table 37, IEEE C57.12.34) are paywalled or were blocked in this session. Most numeric values below are from secondary sources (forums, distributor pages, trade articles) and are marked UNVERIFIED. Do not use any numeric value from this file in a design until it is checked against the purchased standard or the manufacturer's current catalog.

## Tag key

- **[VERIFIED: URL]** - the cited page was fetched, or a search excerpt from an official/manufacturer site states the fact.
- **[UNVERIFIED]** - from a forum, retailer, blog, or my own background knowledge. Needs checking against the primary source.

---

## 1. Lug types

| Type | Installation | Typical use | Notes |
|---|---|---|---|
| Compression, 1-hole (barrel) | Hydraulic/battery crimp with listed die | Feeders, switchgear and breaker terminals, bus-connected cable | Die index embossed on crimp; needs matching tool and die |
| Compression, 2-hole (NEMA pad) | Same as above, pad drilled to NEMA spacing | Transformer and switchgear pads, parallel cable sets | Stud pattern must match the equipment pad |
| Compression, long barrel vs short barrel | Long barrel = more crimps / more conductor strands; short barrel = fewer crimps | Long barrel used where conductor is flexible or the lug is for a larger conductor range; short barrel for compact or space-limited terminations | Crimp count and location are catalog-specified [VERIFIED: https://steinerelectric.com/Product/Burndy-YA292N-HYLUG-2-Hole-Compression-Lug250-kcmilDie-Code-161-2-in-StudCopper-19531 - listing; burndy catalog text on crimp count seen in search excerpt, UNVERIFIED as to layout] |
| Mechanical (set-screw / bolt-type, "mech lug") | Torque on set screw or clamp bolt | Low-current, field-terminated, legacy, or where no crimp tool is available | Torque-critical; NEC Annex I tables cover set-screw torques (UNVERIFIED, see Section 4) |
| Copper | Standard | Most switchgear and transformer terminations | Usually tin-plated for corrosion resistance |
| Aluminum (e.g., 6061-T6) | Compression or mechanical | Aluminum cable, aluminum bus | Must be marked for aluminum or dual-rated; oxide inhibitor used |
| Tin-plated (Cu or Al) | Plated barrel/tongue | Reduces galvanic and oxidation issues | Plating is a finish, not a rating |
| Dual-rated AL9CU | Aluminum body, tin-plated, marked for copper and aluminum conductors, 90 C | Universal lug for mixed or retrofit installations | Morris 6061-T6 tin-plated AL9CU one-hole lug: UL 486B listed, 90 C, 0.56" stud, 1-3/4" NEMA centres, 600 MCM to #2 solid [VERIFIED: https://www.ulegroup.com/products/aluminum-mechanical-lugs-two-conductors-one-hole-mount-600mcm-2-awg]. Whether "AL9CU" is a UL designation or a manufacturer marking is **not confirmed** (UNVERIFIED). |
| Bimetallic (Cu-Al transition) | Factory-bonded Cu/Al transition body | Connects aluminum cable to copper bus or equipment | Vendor claims of friction/explosion-welded transition; factory compound in some (UNVERIFIED vendor claims: https://viox.com, https://frigate.ai) |

**When to use which (general practice, UNVERIFIED):**
- Compression is the default for power cable (>= 4 AWG) in switchgear, transformer and cable bus work.
- Mechanical lugs are acceptable where the conductor range and terminal are both listed for them and no crimp tool is on site.
- Use copper-rated lugs on copper conductors and AL-rated or dual-rated lugs on aluminum. Do not mix without a listed transition.

---

## 2. Standards

| Standard | Scope | Status / notes | Source |
|---|---|---|---|
| UL 486A-486B / CSA C22.2 No. 65 | Wire connectors (solderless, compression, mechanical) | UL 486A-B and CSA C22.2 No. 65 are harmonized. The current CSA edition is C22.2 No. 65:25 (harmonized with NMX-J-543-ANCE-2025 and UL 486A-486B). A new edition is in development with a comment period of 25 Aug - 16 Sep 2026. | [VERIFIED: https://scc-ccn.ca/standards/notices-of-intent/csa-group/wire-connectors-5 - search excerpt; https://webstore.ansi.org/standards/csa/csac22412022 - search excerpt] |
| UL 486E | Equipment wiring terminals for use with aluminum and/or copper conductors | Not confirmed in this session. Some AL9CU lugs are listed only to 486A-B. Check the UL file for the specific catalog number. | UNVERIFIED |
| NEMA CC 1 | Electric power connectors for substations (uninsulated connectors and bus supports, copper or Al) | Latest listed edition ANSI/NEMA CC 1-2018 (R2023). Hole sizes and spacing are in the standard's dimensional tables, which I could not retrieve. Connectors supplied in equipment are generally excluded (governed by equipment standard). | [VERIFIED: https://www.nema.org/standards/view/Electric-Power-Connectors-for-Substations - search excerpt; redirect to makeitelectric.store not followed] |
| 1-3/4 in. (44.5 mm) NEMA hole centres | Common spacing for 1/2 in. stud pads | Confirmed in product listings. Not confirmed as a CC 1 mandate. | [VERIFIED: https://www.ulegroup.com/products/aluminum-mechanical-lugs-two-conductors-one-hole-mount-600mcm-2-awg] (product only) |
| UL 467 / CSA C22.2 No. 41 | Grounding and bonding equipment (clamps, bonding devices, connectors to grounding electrodes) | Harmonized with CSA C22.2 No. 41 and NMX-J-590-ANCE. Current UL 467 edition 11 (dated 29 Apr 2022 per search). Scope references CEC Part I and NEC. Lugs for grounding conductors would fall under connection-equipment categories (interpretation). | [VERIFIED: https://www.csagroup.org/store/product/2422531/ - search excerpt; https://datasheets.globalspec.com/ds/uls/ul-467/2e549cae-5a6f-4b73-a650-363c45fa4afd - search excerpt] |
| ANSI C119.4 | Connectors for Al-Al, Al-Cu, Cu-Cu on distribution and transmission lines (hot-line tests, electrical and mechanical tests) | Latest listed edition ANSI C119.4-2022 (published 22 Dec 2022). Design ratings in the title are Al-Al / Al-Cu <= 93 C, Cu-Cu <= 100 C. Hot-line temperature rise test criteria not retrieved. | [VERIFIED: https://www.nema.org/standards/view/American-National-Standard-for-Electric-Connectors-Connectors-for-Use-Between-Aluminum-to-Aluminum-and-Aluminum-to-Copper - search excerpt] (temperature ratings: UNVERIFIED interpretation of title) |
| CSA C22.2 No. 0.12:19 | Wiring space and wire bending space in enclosures for field-installed wires, <= 750 V | Governs the CSA-side bending-space requirements (CEC Rule 12-3000 / Table 37 pointer). Does not apply to enclosures for conductors smaller than No. 14 AWG. | [VERIFIED: https://www.csagroup.org/store/product/2426601/ - search excerpt] |
| IEEE C57.12.34 / C57.12.28 | Pad-mounted transformer / enclosure requirements, including LV spade and bushing pad dimensions | Could not retrieve the pad-dimension tables. Schneider FAQ says ANSI standard spacing for LV spade tabs on padmount transformers is 1-3/4 in. for 2 to 4 spade lug pads (fetch returned 404; search excerpt only). | [UNVERIFIED: https://www.se.com/us/en/faqs/FA99406 - search excerpt] |

**Not yet checked (open):** NEMA CC 1 dimensional tables; UL 486A-B torque tables and their current numbering; UL 486E scope; C57.12.34 pad figures; NEMA TR 1 spade dimensions.

---

## 3. Number of lugs per phase, conductor sizes, and bending space

### 3.1 Parallel conductor sets
- Parallel conductor counts are set by the equipment terminal and feeder design, not by the lug alone. Each lug must be listed for the conductor size (or range) it carries, and the equipment must be listed for the total termination count.
- NEC 310.10(H) governs parallel conductors (UNVERIFIED section number; check edition).
- CEC equivalent: Section 4 and parallel-conductor rules (UNVERIFIED section number).

### 3.2 Lug quantity per terminal
- The count of lugs per phase is the number of conductor sets (parallel runs) that terminate on that phase pad or terminal. Each run needs its own listed lug, or a multi-conductor lug listed for the combination.
- Check the equipment's "wires per terminal" marking and the lug's listed conductor range.
- Pad hole pattern (see 3.3) limits how many lugs physically fit.

### 3.3 Pad and hole patterns
- NEMA spacing: 1/2 in. stud, 1-3/4 in. hole centres (common for 2-hole and 4-hole pads). [VERIFIED: https://www.ulegroup.com/products/aluminum-mechanical-lugs-two-conductors-one-hole-mount-600mcm-2-awg] and [VERIFIED: https://www.gexpro.com/p/742939/burndy/compression-lug-2-hole-250-600-mcm/781810290293/ya36a3n131td12e - listing, search excerpt]
- Transformer LV spade: 1-3/4 in. centres for 2 to 4 spade lug pads (UNVERIFIED, see Section 2).
- ABB/Homac adapters: 9/16 in. (0.562 in.) holes on 1-3/4 in. centres, NEMA pad first hole centre at 0.825 in. [VERIFIED: https://empower.abb.com/ecatalog/ec/EN_NA/p/CTSC12 - product page, search excerpt; hole and spacing text as in search excerpt]

### 3.4 Wire bending space (NEC 312.6 / CEC Table 37)
- **NEC 312.6(A)** applies where conductors do not enter or leave through the wall opposite their terminals. **NEC 312.6(B)** applies to conductors entering from the opposite wall, with Table 312.6(B) giving the minimum space by conductor size and "wires per terminal."
- Table 312.6(B) has columns for 1, 2, 3 and 4+ conductors per terminal. Lay-in terminals can have reduced space (superscript notes). Note 3 addresses compact-stranded aluminum. [VERIFIED: https://iaeimagazine.org/2014/januaryfebruary-2014/articles-312-and-314/ - fetched]
- Example from ECM (UNVERIFIED, forum/trade): 300 kcmil terminal values of 10 in. (1-2 conductors), 11 in. (3), 12 in. (4+). The source mislabels the size; check the table directly.
- Measurement is perpendicular to the wall, from the end of the lug/connector to the wall or obstruction (UNVERIFIED, from forum summary).
- For switchgear and panelboards, the manufacturer certifies 312.6 compliance based on the largest lug the enclosure accepts (UNVERIFIED, trade article).
- **CEC equivalent:** CSA C22.2 No. 0.12:19 (wiring space and wire bending space) and CEC Part I Rule 12-3000 / Table 37 (pointer). The CEC table values were not retrieved. [VERIFIED: https://www.csagroup.org/store/product/2426601/ - scope]

### 3.5 UL 891 / UL 1558 bending space
- UL 891 (switchboards) and UL 1558 (metal-enclosed low-voltage power circuit breaker switchgear) include wire bending space and terminal requirements. Not retrieved in this session. Treat as UNVERIFIED.

### 3.6 Transformer terminal pads
- IEEE C57.12.34 (pad-mounted, three-phase, MV) and C57.12.28 (enclosure integrity) define terminal and pad arrangements. Dimensions not retrieved. UNVERIFIED.

---

## 4. Torque, hardware, and surface prep

### 4.1 UL 486A-B torque tables
- UL 486A-B contains torque tables for screws and set screws. Forum discussion says Table 21 (the NEC Annex I source) has A and B columns. A = current cycle test; B = other tests. Example values reported (UNVERIFIED, forum): AWG 30-10 gives 15 lbf-in (A) vs 20 lbf-in (B). [UNVERIFIED: https://forums.mikeholt.com/threads/table-21-tightening-torque-for-screws.146421/latest - search excerpt; fetch returned 403]
- Burndy cut sheets refer to UL 486 Tables 7-4, 7-5, 7-6 for smaller sizes. Table numbering varies by edition. [UNVERIFIED: https://forums.mikeholt.com/threads/torque-values-consult-ul486-tables-7-4-7-5-7-6.2555267/latest - search excerpt]
- Manufacturer marked torque governs. Lugs are commonly marked with a clockwise torque value. [UNVERIFIED: vendor text in search excerpt, https://lugsdirect.com/guide-on-torque-tightening-technique.html]

### 4.2 NEC Annex I
- NEC Annex I contains recommended torque tables for electrical connections (I1 slotted screws >= 10, I2 slotted screws <= 8 and <= 8 AWG wire, I3 hex/square key set screws). Secondary source only. UNVERIFIED.

### 4.3 Stud and bolt torque data (distributor/vendor)
- Panduit LCCX4/0-38D-X on 3/8 in. stud: 20-25 ft-lb (vendor listing). [UNVERIFIED: https://www.ipsecuritydepot.com/cu-lug-2h-4-0-flex-3-8-stud/lccx4-0-38d-x/]
- Panduit 4/0 lug, 1/2 in. stud: 120 in-lb listed; looks low for 1/2 in. stud, conflicts with other listings. UNVERIFIED, needs catalog check.
- 1/4 in. stud: 20-35 ft-lb in one listing. UNVERIFIED.
- Rule of thumb only: a bolt-torque value depends on grade, lubrication, plating, and stud material. **Always use the equipment or lug manufacturer's value.**

### 4.4 Hardware
- Use a grade and plating matching the equipment spec (commonly SAE Grade 5 or 8, or ASTM A325 for structural). UNVERIFIED general practice.
- Belleville (conical) washers are used on aluminum connections to maintain clamp load as the joint creeps. UNVERIFIED general practice; confirm in the manufacturer's instructions.
- Re-torque after the first heat cycles and at periodic inspection, especially on aluminum. UNVERIFIED general practice.

### 4.5 Contact surface prep and joint compound
- Clean and wire-brush contact surfaces, apply oxide inhibitor (joint compound) for aluminum, and use compound only where listed for the lug and conductor. Vendor claims: zinc-particle compounds cut oxide (UNVERIFIED). [UNVERIFIED: https://nassaunationalcable.com/collections/pan-lug-contact-aid-joint-compound/products/pan-lug-aluminum-connection-contact-aid-joint-compound-8-oz-cmp-200-1]
- Aluminum-to-copper: use bimetallic lugs or a listed transition. Do not connect bare Al directly to Cu bus. Galvanic risk in moisture (UNVERIFIED general practice).
- NEC 110.14(B) requires conductors and terminations to be compatible for the conductor material (copper/aluminum) (UNVERIFIED section; check edition).

---

## 5. Manufacturer selection data

| Vendor | How the catalog selects a lug | Verified data |
|---|---|---|
| Burndy (HYLUG) | Conductor size + stud size -> part no. and **die index** (e.g., 1/0 Cu 1-hole, 5/16 in stud = die 12; 3/0 1-hole, 1/2 in = die 14; 2 AWG 2-hole, 1/2 in = die 10; 250 kcmil 2-hole, 1/2 in = die 16; 2/0 2-hole, 3/8 in = die 13; 2/0 2-hole, 1/2 in = die 13). Tooling and crimp count per listing. Install sheets carry torque. | [VERIFIED: https://steinerelectric.com/Product/Burndy-YA25-HYLUG-1-Hole-Compression-Lug1-0-AWGDie-Code-125-16-in-StudCopper-19519 - distributor listing, die codes]. Torque: not retrieved. |
| Thomas & Betts / ABB Installation Products (Homac, CTSC / TSC series) | Part numbers by conductor and stud; NEMA pad adapters with 1-3/4 in. centres | [VERIFIED: https://empower.abb.com/ecatalog/ec/EN_NA/p/CTSC12 - product page, search excerpt]. Catalog tables not retrieved. |
| Panduit (LCCX, LCD, LCAx series) | Part no. by conductor and stud; tool and die (e.g., CT-900 / P23 for 8 AWG, CT-940CH / P1000 for LCCX4/0) | Distributor listings only. UNVERIFIED. |
| ILSCO (CCL, CSWS, CLSH) | Part no. by conductor and stud (e.g., CSWS-1/0-12 = 1/0 Cu, 1/2 in. stud) | Distributor listings only. UNVERIFIED. ILSCO torque chart not retrieved. |
| Morris / ULE (AL9CU) | Part no. by conductor range and stud; AL9CU marking | [VERIFIED: https://www.ulegroup.com/products/aluminum-mechanical-lugs-two-conductors-one-hole-mount-600mcm-2-awg] |

**Action:** To populate the selection algorithm with real values, download current Burndy, Panduit and ILSCO catalogs (conductor x stud x die tables) and their installation sheets (torque). These are the only reliable inputs for the algorithm.

---

## 6. NEC vs CEC differences

| Topic | NEC (NFPA 70) | CEC Part I (CSA C22.1) | Notes |
|---|---|---|---|
| Terminal temperature limit | NEC 110.14(C); default 60 C for equipment rated <= 100 A or marked for conductors <= 1 AWG (UNVERIFIED sub-numbering; check edition) | Rule 4-006 (2018 ed. quoted in IAEI article): Subrule 2 default 60 C for equipment rated <= 100 A or marked for No. 1 AWG or smaller; 75 C for > 100 A or larger than No. 1 AWG. [VERIFIED: https://iaeimagazine.org/columns/canadian/application-of-rule-4-006-of-the-canadian-electrical-code/ - fetched] | Thresholds look similar; section structure and wording differ. Confirm against current NEC and CEC editions. |
| Limit length | NEC 110.14(C) (no explicit 1.2 m length in secondary summaries; UNVERIFIED) | Rule 4-006 Subrules 1-2 apply only to the first 1.2 m of conductor from the point of termination; cable transitions must give at least 1.2 m of conductor on the equipment (Subrule 5). [VERIFIED: same IAEI URL] | Important difference for layout. |
| Ampacity vs termination | Ampacity from Table 310.16 / 310.15(B)(16); terminations limit | Ampacity from Tables 1-4 and Rule 4-004; Rule 4-006 "not intended to address conductor allowable ampacity" (App. B). [VERIFIED: same IAEI URL] | Rule 4-004(7) correction factors apply in addition to 4-006. |
| Wire bending space | NEC 312.6 and Table 312.6(A)/(B) | CSA C22.2 No. 0.12:19 and CEC Rule 12-3000 / Table 37 (table values not retrieved) | Do not assume NEC table values apply in Canada. |
| Connector standards | UL 486A-B, UL 486E, UL 467 | CSA C22.2 No. 65 (harmonized with UL 486A-B), CSA C22.2 No. 41 (harmonized with UL 467) | Harmonized, but check each listing for the CSA mark. |
| Grounding and bonding | NEC 250 + UL 467 | CEC Section 10 + CSA C22.2 No. 41 (section number UNVERIFIED) | |
| Substation connectors | NEMA CC 1, ANSI C119.4 | Same standards referenced in CSA practice (UNVERIFIED) | |

---

## 7. Selection algorithm (for implementation)

### 7.1 Inputs
1. `conductor_material` - Cu | Al | CuAl-mixed
2. `conductor_size` - AWG / kcmil; `conductor_stranding` - solid | stranded | compact
3. `parallel_sets` - integer per phase
4. `terminal_rating_C` - 60 | 75 | 90 (from equipment marking; default per Section 6 if unmarked)
5. `equipment_rating_A` - breaker frame / bus rating (drives default temperature)
6. `pad_type` - 1-hole barrel | 2-hole NEMA | 4-hole NEMA | LV spade | bus stud (size)
7. `stud_size_in` - e.g., 3/8, 1/2, 9/16
8. `tool_available` - hydraulic | battery | mechanical | none
9. `jurisdiction` - NEC | CEC
10. `environment` - indoor | outdoor | wet | corrosive

### 7.2 Steps
1. **Check temperature limit.** Lowest equipment rating at termination (or default per jurisdiction). Use that column for conductor ampacity (NEC 110.14(C) / CEC 4-006). Fail if conductor ampacity at that column < required current.
2. **Check material compatibility.** If `conductor_material` = Al, lug must be marked AL or dual-rated (AL9CU or listed Cu-Al). If mixed, require bimetallic or listed transition. (NEC 110.14(B), UNVERIFIED section.)
3. **Choose lug family.**
   - If `tool_available` in {hydraulic, battery} and size >= 4 AWG -> compression.
   - Else if mechanical lug is listed for the conductor range -> mechanical.
   - Else -> fail, request tool.
4. **Choose lug stock.** Look up catalog row by (vendor, conductor_size, conductor_material, stud_size, pad_type). Gives part no., die index, crimp count, listed conductor range.
5. **Quantity per phase.** `lugs_per_phase = parallel_sets` (one listed lug per conductor set), unless a multi-conductor lug is listed for the combination. Confirm lugs fit the pad pattern and the bending space for `wires_per_terminal = lugs_per_phase`.
6. **Bending space check.** Look up Table 312.6(B) (NEC) or CEC Table 37 for conductor size and `wires_per_terminal`. Compare to cabinet depth minus clearance. Fail -> increase enclosure depth, change entry wall, or use a lay-in terminal (per table notes).
7. **Bolt / stud size.** From the lug part (stud_size_in) and pad. Must match equipment stud. Set hardware grade and washer per equipment spec.
8. **Torque.** Use the lug marked torque or the catalog torque for that part number (preferred). Fallback: UL 486A-B table value for the stud/size (flag as UNVERIFIED until checked). Record torque source.
9. **Surface prep and compound.** Required for Al: clean, brush, apply listed compound. Required for Cu-Al: bimetallic only.
10. **Output.** `{lug_part, vendor, die_index, crimps, qty_per_phase, stud_size_in, hardware_grade, washer, torque_ftlb_or_inlb, torque_source, bending_space_required_in, bending_space_available_in, temperature_column_C, jurisdiction, flags[]}`.

### 7.3 Pseudocode (sketch)
```
def select_lug(inp):
    temp = inp.terminal_rating_C or default_temp(inp.jurisdiction, inp.equipment_rating_A, inp.conductor_size)
    if conductor_ampacity(inp.conductor_size, inp.conductor_material, temp) < inp.load_A / inp.parallel_sets:
        fail("ampacity at terminal temperature")
    if inp.conductor_material == "Al": require_marking(["AL", "AL9CU"])
    if mixed: require_bimetallic()
    family = "compression" if inp.tool_available in ("hydraulic", "battery") and size_awg >= 4 else "mechanical"
    lug = catalog_lookup(vendor=inp.vendor_pref, size=inp.conductor_size, material=inp.conductor_material,
                         stud=inp.stud_size_in, pad=inp.pad_type, family=family)
    qty = inp.parallel_sets
    space_req = bending_space_table(inp.jurisdiction, inp.conductor_size, wires_per_terminal=qty)
    if space_req > inp.cabinet_space_available_in: flag("bending space")
    torque = lug.marked_torque or ul486_torque(lug.stud, lug.conductor) or fail("no torque source")
    return Selection(...)
```

**Known gaps for the algorithm:** conductor ampacity tables (NEC 310.16 / CEC Tables 1-4 not retrieved); bending-space tables; torque values per part; default-temperature thresholds in NEC section form.

---

## Open questions / needs checking

1. Exact NEC 110.14(C) subsections (current NEC edition) and the NEC default 60 C threshold wording. Compare with CEC Rule 4-006 (2018 ed. text confirmed; current edition check needed).
2. CEC Rule 12-3000 and Table 37 values; CSA C22.2 No. 0.12:19 table values.
3. NEC Table 312.6(B) values and footnotes (superscripts a-e; Note 3 aluminum).
4. UL 486A-B torque tables (current edition numbering) and whether Table 21 / Annex I values match.
5. What "AL9CU" means: UL designation or manufacturer marking? Confirm via UL Product iQ listing.
6. UL 486E scope and whether AL9CU lugs need 486E in addition to 486A-B.
7. NEMA CC 1 hole pattern and dimensional tables for 1/2 in. stud and 1-3/4 in. centres.
8. ANSI C119.4 hot-line temperature-rise test acceptance criteria (2022 edition).
9. IEEE C57.12.34 and C57.12.28 LV spade and bushing pad drawings; NEMA TR 1 dimensions.
10. Burndy, Panduit, ILSCO catalog die and torque tables (download current catalogs and install sheets).
11. Compression die index is required for inspection; confirm the crimp-marking requirement in UL 486A-B and CSA C22.2 No. 65.
12. Bimetallic lug listing (UL 486B / CSA) and whether factory-filled compound is covered by the listing.
13. Bolt grade and Belleville washer requirements in the manufacturer install sheets; check whether NEC or CEC requires them.
14. Several tool calls to ECM (Charles Miller articles), Mike Holt forums and Schneider FAQ returned 403 or 404 or redirect loops. Retry with a different route or purchased copies.
15. UL 891 and UL 1558 bending-space and terminal requirements for switchboards and switchgear.

---

## Sources

Fetched or search-excerpt (VERIFIED):
- https://iaeimagazine.org/columns/canadian/application-of-rule-4-006-of-the-canadian-electrical-code/ (fetched; CEC Rule 4-006, 2018 ed.)
- https://iaeimagazine.org/2014/januaryfebruary-2014/articles-312-and-314/ (fetched; NEC 312.6, Tables 312.6(A)/(B))
- https://www.ulegroup.com/products/aluminum-mechanical-lugs-two-conductors-one-hole-mount-600mcm-2-awg (fetched; AL9CU lug data)
- https://scc-ccn.ca/standards/notices-of-intent/csa-group/wire-connectors-5 (search excerpt; CSA C22.2 No. 65:25)
- https://www.nema.org/standards/view/Electric-Power-Connectors-for-Substations (search excerpt; NEMA CC 1 scope)
- https://www.nema.org/standards/view/American-National-Standard-for-Electric-Connectors-Connectors-for-Use-Between-Aluminum-to-Aluminum-and-Aluminum-to-Copper (search excerpt; ANSI C119.4 scope)
- https://www.csagroup.org/store/product/2422531/ (search excerpt; CSA C22.2 No. 41)
- https://datasheets.globalspec.com/ds/uls/ul-467/2e549cae-5a6f-4b73-a650-363c45fa4afd (search excerpt; UL 467)
- https://www.csagroup.org/store/product/2426601/ (search excerpt; CSA C22.2 No. 0.12:19)
- https://steinerelectric.com/Product/Burndy-YA25-HYLUG-1-Hole-Compression-Lug1-0-AWGDie-Code-125-16-in-StudCopper-19519 (search excerpt; Burndy die codes)
- https://empower.abb.com/ecatalog/ec/EN_NA/p/CTSC12 (search excerpt; ABB NEMA spacing)

Secondary (UNVERIFIED):
- https://forums.mikeholt.com/threads/table-21-tightening-torque-for-screws.146421/latest
- https://forums.mikeholt.com/threads/torque-values-consult-ul486-tables-7-4-7-5-7-6.2555267/latest
- https://forums.mikeholt.com/threads/bend-space-requirements.127195/
- https://forums.mikeholt.com/threads/nec-table-312-6-b.147292/latest
- https://forums.mikeholt.com/threads/312-6-wire-bending-space-at-terminals.2588385
- https://forums.mikeholt.com/goto/post?id=1390424 (110.14(C) discussion)
- https://www.ecmag.com/magazine/articles/article-detail/codes-standards-general-installation-requirements-part-ix (403 on fetch; search excerpt)
- https://www.ecmag.com/magazine/articles/article-detail/codes-standards-temperature-limitations-electrical-connections-part-ii (403 on fetch; search excerpt)
- https://www.ipsecuritydepot.com/cu-lug-2h-4-0-flex-3-8-stud/lccx4-0-38d-x/ (retailer torque)
- https://www.gexpro.com/p/742939/burndy/compression-lug-2-hole-250-600-mcm/781810290293/ya36a3n131td12e (retailer)
- https://lugsdirect.com/guide-on-torque-tightening-technique.html (vendor guide)
- https://viox.com/ (bimetallic lug vendor)
- https://nassaunationalcable.com/ (joint compound vendor)
- https://www.se.com/us/en/faqs/FA99406 (1-3/4 in. spade spacing; page returned 404 on fetch)
- https://www.ascopower.com/us/en/resources/technical-briefs/why-cable-bend-space-matters.jsp (redirect to se.com; not followed)
- https://www.makeitelectric.store/us (redirect loop; not usable)
