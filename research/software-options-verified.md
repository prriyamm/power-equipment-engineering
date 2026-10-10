# Software options for manufacturing design calculations (US and Canada)

Research date: 2026-10-10. Scope: cable ampacity and sizing, lug and termination checks, cable bus ampacity, magnetic fields, busbar temperature rise and short-circuit bracing, transformer design. Standards: IEEE, NEC (NFPA 70), CEC (CSA C22.1), UL, CSA.

**Tagging rules used below**
- `[VERIFIED: URL]`: the fact appears on the cited page, as fetched on 2026-10-10 or quoted in a search excerpt.
- `[UNVERIFIED]`: from general knowledge, a forum post, or a failed fetch. Check before relying on it.
- Forum posts are labelled as opinions. Prices are only listed when a vendor published them. None were found, so every price is "contact sales" or "unknown".

**Headline findings**
1. No commercial system-study tool checked so far clearly supports CSA C22.1 (CEC) cable ampacity. ETAP and SKM's cable modules list NEC and IEC standards, not CSA or CEC. EasyPower lists NEC and ANSI. This is the most important gap for a Canadian-facing manufacturer.
2. The CEC ampacity logic (Tables 1 to 4, 5A, 5C, D3 and termination rules) will likely need an internally validated calculator or a spreadsheet, whatever commercial tool is bought.
3. For magnetic fields, eddy-current losses, and busbar or winding hotspots, the realistic options are COMSOL AC/DC with Heat Transfer, Simcenter MAGNET or Flux, and Ansys Maxwell with Icepak. Free options are FEMM, Elmer, GetDP, and OpenFOAM for thermal work.
4. For early transformer and inductor design, OpenMagnetics (open source) is a credible free starting point. It is early-stage, and its current state is unverified.
5. Pricing is "contact sales" for nearly every commercial tool. A vendor quote is needed before any budget comparison.

---

## 1. System and cable tools

| Tool (vendor) | Relevant calculations | NEC | CSA / CEC | Platform | Licence and price | Trial | Notes |
|---|---|---|---|---|---|---|---|
| ETAP (ETAP) | Cable ampacity and derating, cable sizing, voltage drop, short circuit, arc flash (module availability per package) | Yes [VERIFIED: https://etap.com/packages/cable-ampacity] | **No CSA or CEC listed** [VERIFIED: https://etap.com/packages/cable-ampacity, https://etap.com/product/cable-sizing] | Windows [UNVERIFIED] | "Get Pricing" only [VERIFIED: https://etap.com/packages/cable-ampacity] | Free 30-day trial [VERIFIED: https://etap.com/packages/cable-ampacity] | Standards listed: IEC 60502, IEC 60364, IEC 60092, NEC, ICEA P-54-440, IEEE 399, BS 7671, NF C15-100, AS/NZS 3008. Industry standard. |
| SKM PowerTools, Cable Ampacity module (SKM Systems Analysis) | Ampacity and temperature rise per IEC 60287, with Neher-McGrath where IEC 60287 does not apply | Not stated on the page [VERIFIED: https://skm.com/cable-ampacity.html] | **No CSA or CEC mentioned** [VERIFIED: https://skm.com/cable-ampacity.html] | Windows [UNVERIFIED] | "Get Pricing" link only; no price [VERIFIED: https://skm.com/cable-ampacity.html] | Request demo; no trial stated [VERIFIED: https://skm.com/cable-ampacity.html] | Module name confirmed as "Cable Ampacity module" (the search result's "CAPE" name was not confirmed). Page says "New for PTW Version 8.0". |
| EasyPower (Bentley Systems) | Short circuit (ANSI and IEC), arc flash, protection and coordination, power flow, harmonics. **No cable sizing listed.** | NEC rules and ANSI [VERIFIED: https://www.easypower.com/] | No CSA or CEC mentioned [VERIFIED: https://www.easypower.com/] | Windows [VERIFIED: https://www.easypower.com/] | Bentley SES licence; sold via Bentley eStore; tiers Base to Advanced; no prices shown [VERIFIED: https://www.easypower.com/] | "Pricing and Demo" link; no trial stated [VERIFIED: https://www.easypower.com/] | Forum opinion (dated, roughly 2009 to 2011, not current): "about half of ETAP's price"; "prefer Easypower" [UNVERIFIED: Mike Holt forum search excerpts, https://forums.mikeholt.com/threads/skm-easypower-or-etap.96106/latest]. |
| DIgSILENT PowerFactory | Short-circuit analysis, cable analysis, arc flash. IEC 60909 and ANSI not confirmed on the page. | Not stated | Not stated | "Fully Windows compatible" [VERIFIED: https://www.digsilent.de/en/powerfactory.html] | Quote request; editions not described; no price [VERIFIED: https://www.digsilent.de/en/powerfactory.html] | Demo request; no free trial stated | Strong for utility and grid studies. Probably over-scoped for plant-level manufacturing. |
| CYME / CYMCAP (Eaton) | Steady-state and transient cable thermal rating; IEC 60287, IEC 60228, IEC 60853; Neher-McGrath | Not stated | Not stated | Not verified (fetch failed) | Not found; contact Eaton [UNVERIFIED] | Not found | Eaton markets CYMCAP as the reference for cable thermal rating [VERIFIED search excerpt: https://www.eaton.com/us/en-us/catalog/software/power-cable-ampacity-software.html]. Page fetch failed (timeout), so details are excerpt-based only. |
| Paladin DesignBase | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | **Not verified.** Site fetch failed (HTTP 522), then redirected to an unrelated domain (not followed). |
| ElecCalc | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | **Not researched.** |
| Design Master Electrical | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | **Not researched.** |
| Trimble / ProDesign | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | **Not researched.** |
| Schneider Ecodial (IEC) | Expected: LV cable sizing, short circuit | Unknown | Unknown | Unknown | Unknown | Unknown | **Not verified.** Pages returned 404 or no DNS. Treat as IEC-only [UNVERIFIED]. |
| ProCalc / Southwire voltage drop calculator | Voltage drop, conductor sizing | Unknown | **CEC coverage not confirmed** | Web and app [UNVERIFIED] | Free [UNVERIFIED] | n/a | Search did not return a result. |
| Mike Holt tools | NEC conductor and ampacity tools | NEC-based [UNVERIFIED] | No CEC [UNVERIFIED] | Not verified | Not verified (forum page returned 403) | n/a | Mike Holt site did not show an ampacity product [VERIFIED: https://www.mikeholt.com/, no product found]. |

**Which tools do CEC cable sizing?**
- None confirmed. ETAP, SKM Cable Ampacity, and EasyPower list no CSA or CEC support on their pages (see above).
- A CEC-specific engineering tool was not found. Search returned articles and generic charts only [VERIFIED search excerpts: https://electricalindustry.ca/latest-articles/a-code-based-approach-to-cable-sizing/]. Points that search excerpts support: the CEC ampacity tables are based on 30 °C ambient, Table 5A gives the ambient correction, the termination rating governs, and the 2024 edition added Table D3 for voltage drop [VERIFIED search excerpts only; confirm against the printed code].

---

## 2. Cable bus and busway

| Item | Finding | Status |
|---|---|---|
| MP Husky cable bus | Catalog states ratings are based on NEC and ICEA tables at 90 °C conductor and 40 °C ambient, and that the cable bus system is certified to CSA C22.2 No. 27 and No. 201 and to UL standards. No online ampacity calculator found. | [VERIFIED search excerpt: https://pdf.archiexpo.com/pdf/mp-husky/cable-bus/149710-264272.html]; calculator absence is UNVERIFIED |
| Superior Tray and other manufacturers | Not researched. | Open question |
| NEC coverage | NEC Article 368 (busways) and Article 370 (cable bus) — the search did not confirm the current article numbers. | [UNVERIFIED] |
| Neher-McGrath basis | Neher-McGrath assumes 20 °C soil at 36 in depth and 90 K·cm/W soil thermal resistivity. Those are assumptions, not field conditions. | [VERIFIED search excerpt: https://www.allumiax.com/blog/neher-mcgrath-study-of-cables-in-power-system] |

Busbar temperature rise and short-circuit bracing are not covered by any tool above. Treat these as open questions (section 7).

---

## 3. FEA and product design

| Tool (vendor) | Relevant capability | Platform | Licence and price | Trial | Notes |
|---|---|---|---|---|---|
| ANSYS Maxwell and Icepak (now part of Synopsys) | Maxwell: low-frequency EM field solver for transformers, busbars and inductors, including AC losses, nonlinear and temperature-dependent materials. Icepak: thermal, coupled from Maxwell losses. Leakage inductance is not explicitly addressed for transformers. | Within Ansys Electronics Desktop (AEDT); Windows and Linux support [UNVERIFIED] | Pricing not shown. Annual maintenance is typical (third-party review) [UNVERIFIED]. Ansys Student bundle is free for students [VERIFIED: https://ansys.synopsys.com/products/electronics/ansys-maxwell] | "Free Trials" link [VERIFIED: https://ansys.synopsys.com/products/electronics/ansys-maxwell] | Ansys is now under Synopsys (redirect verified). Note: an earlier search excerpt said "Siemens acquired Ansys". That is wrong. |
| Simcenter MAGNET (Siemens) | Low-frequency EM: transformers, electrical machines, actuators. AC losses, proximity effect, hysteresis, nonlinear and temperature-dependent materials. Built-in FE thermal solver for steady-state and transient temperature with winding and core losses. Electric-field analysis for insulation. | Not specified | "Contact us for sales and pricing" [VERIFIED: https://www.siemens.com/en-us/products/simcenter/electromagnetics-simulation/magnet/] | None mentioned | Busbars are not listed as a capability (only a blog link). ThermNet is not mentioned on the page. Thermal coupling is built in. |
| Simcenter Flux (Siemens; formerly Altair Flux?) | Low-frequency EM for motors, sensors, power devices. 2D, skewed and 3D. Thermal and multiphysics linking. Transformers not mentioned. | Not specified | "Contact us" [VERIFIED: https://www.siemens.com/en-us/products/simcenter/electromagnetics-simulation/flux/] | None mentioned | The "formerly Altair Flux" link is **UNVERIFIED**. The altair.com/flux URL redirected to the Siemens Simcenter page (redirect verified), but the Siemens page does not mention Altair. |
| COMSOL Multiphysics AC/DC Module + Heat Transfer Module | Magnetostatics and AC electromagnetics: skin and proximity effects, conductor losses, litz wire, Steinmetz and Bertotti core loss, Lorentz forces. Thermal coupling through the Heat Transfer Module (required for busbar temperature rise). Induction heating listed. | Windows, Linux, macOS [UNVERIFIED] | "Contact sales" [VERIFIED: https://www.comsol.com/acdc-module] | Free trial typically available [UNVERIFIED] | Best-fit general tool for busbar eddy and temperature rise. Licence per module. |
| JMAG (JSOL) | Motor-focused EM and thermal. Transformer and reactor listed as an application, with impedance and nonlinear material analysis. | Not specified; web version JMAG-Express Online | Not shown on the page | Free trial available [VERIFIED: https://www.jmag-international.com/] | Motor design is its main focus. Weak fit for transformers and busbars. |
| FEMM (free, David Meeker) | Magnetics, electrostatics, heat flow, current flow (2D). | Windows-focused [UNVERIFIED: page did not state platform] | Free [UNVERIFIED] | n/a | Best free 2D magnetic-field tool for quick checks. Thermal is basic. |
| Elmer FEM | Multiphysics FEM incl. electromagnetics and heat | Linux, Windows [UNVERIFIED] | GPL [UNVERIFIED] | n/a | Fetch failed (403). Not verified. |
| GetDP / ONELAB | Open FE solver originally for EM; steady, transient, time-harmonic in 1D to 3D; thermal conduction example | Windows 10+, Linux (glibc 2.24+), macOS [VERIFIED: https://getdp.info/] | GPL v2+; latest stable 3.5.0 (May 2022) [VERIFIED: https://getdp.info/] | n/a | Steeper learning curve (.pro files). Good for custom EM formulations. |
| OpenFOAM | CFD incl. turbulence and heat transfer; electromagnetics claimed [VERIFIED: https://www.openfoam.com/] | Linux, macOS, Windows downloads [VERIFIED: https://www.openfoam.com/] | Open source; licence not stated on openfoam.com page [UNVERIFIED: likely GPL] | n/a | Use for forced-air or oil-cooling flows, not for basic busbar conduction. Two forks exist (OpenCFD vs OpenFOAM Foundation). |

---

## 4. Transformer design

| Tool | Notes | Status |
|---|---|---|
| OpenMagnetics (MKF engine, PyOpenMagnetics wrapper) | Free, open-source design tool for transformers and inductors. Claims more than 40 models for air-gap reluctance, core and winding losses, leakage inductance, temperature rise, plus creepage, clearance, and withstand voltage. PyOpenMagnetics is MIT licensed. Early-stage as of 2023. | [VERIFIED search excerpts: https://www.how2power.com/newsletters/2303/products/H2PToday2303_products_OpenMagnetics.pdf?NOREDIR=1, https://github.com/gpitel/PyMKF]. Current status UNVERIFIED. |
| FEMMT (Paderborn University) | Python FEM toolbox for inductors and transformers | [VERIFIED search excerpt: https://www.vde-verlag.de/proceedings-en/565822103.html] |
| Ansys Maxwell with Icepak | Transformer loss and thermal workflow; automated modelling from tabular inputs (PyAEDT webinar) | [VERIFIED: https://ansys.synopsys.com/products/electronics/ansys-maxwell] |
| Commercial manufacturer tools (in-house) | Large OEMs (for example Hitachi Energy, Siemens Energy, GE Vernova) use proprietary design systems. None is available to buy. | [UNVERIFIED] |
| Other commercial magnetics tools (Infolytica MagNet, SPEED) | Listed in background knowledge only. | [UNVERIFIED] |
| Elecsys "Smart Transformer" | Could not confirm this product exists. | [UNVERIFIED: search failed] |

---

## 5. Open-source power-system libraries

| Library | Short-circuit | Cable ampacity or thermal derating | Licence | Notes |
|---|---|---|---|---|
| pandapower | Short-circuit module exists [VERIFIED: https://pandapower.readthedocs.io/en/latest/]. IEC 60909 not confirmed by the fetched page. | Not mentioned on the fetched page; treat as not supported. | BSD (licence not confirmed on page) [UNVERIFIED] | Python. Good for network analysis and scripting. Not a cable thermal tool. |
| PyPSA | Not confirmed (docs site redirect; first fetch 404) | Not supported [UNVERIFIED] | Open source, MPL-2.0 [UNVERIFIED] | Built for transmission planning and optimal power flow. Weak fit for plant-level cable design. |
| OpenDSS (EPRI) | Fault studies: all-bus fault study, single-snapshot faults, Monte Carlo [VERIFIED: https://opendss.epri.com/FaultStudies.html] | Ratings are inputs (Normamps and Emergamps) [UNVERIFIED] | Open source, EPRI release 2008 [VERIFIED: https://opendss.epri.com/BriefHistoryandObjectives.html per search excerpt] | Distribution-focused. Good for scripting and scenario studies. |
| GridCal | Short-circuit including IEC 60909 [UNVERIFIED] | Not verified | Open source [UNVERIFIED] | Not researched further. |

Use these libraries for network-level checks. Cable ampacity still needs a thermal engine such as IEC 60287 or Neher-McGrath, implemented in-house or bought.

---

## 6. Recommendation for this manufacturer

**Context:** US and Canadian product lines (transformers, switchgear, cable bus). Priority is design calculations for manufacturing. Linux workstation; Windows is available for commercial tools.

### Budget tier (lowest outlay, most work in-house)
- **Core calculations:** Python and spreadsheets. Build and validate NEC (Article 310) and CEC (Tables 1 to 4, 5A, 5C, D3) ampacity and voltage-drop checks. Check every table value against the printed code. This is the only route to CEC coverage with the tools found so far.
- **Thermal engine:** IEC 60287 or Neher-McGrath, implemented in-house from the published standard. Verify against a vendor example.
- **Magnetics and busbar fields:** FEMM for 2D quick checks; GetDP (or Elmer) for custom formulations on Linux.
- **Transformer early design:** OpenMagnetics (PyOpenMagnetics) as a starting point, with results checked by hand.
- **System studies (optional):** a single seat of EasyPower or SKM if short-circuit or coordination work is needed. Get a quote first (no public pricing). Verify CEC support with the vendor in writing before buying; neither vendor lists CSA or CEC.
- **Estimated cost:** open source plus engineering time, plus one commercial system-study licence (price unknown, get a quote).

### Premium tier (validated commercial tools, faster iteration)
- **Electromagnetics and thermal:** COMSOL AC/DC Module + Heat Transfer Module (Linux and Windows support to be confirmed). Strong fit for busbar temperature rise, eddy losses, and magnetic forces. Pricing is contact-sales.
- **Alternative:** Simcenter MAGNET (transformer and electrical-machine focus, built-in thermal) if the team is already on Siemens tools. Pricing is contact-sales.
- **Transformer-specific FEA:** Ansys Maxwell and Icepak via AEDT if the team already uses Ansys. Pricing is contact-sales; the Ansys licence now sits under Synopsys.
- **System studies:** ETAP (30-day free trial, strong market presence) or SKM PowerTools (Cable Ampacity module). Neither lists CSA or CEC, so the CEC cable sizing still needs an in-house calculator.
- **Validation:** run the in-house CEC calculator against a vendor's example set before use.

**Key decision for the manufacturer:** Because no tool found handles CEC cable ampacity, the first purchase should not be a cable-ampacity package. Build and validate the in-house CEC calculator first. Then decide between COMSOL and Simcenter for the field work.

---

## 7. Sources

Vendor pages (fetched 2026-10-10 unless noted):
- https://etap.com/packages/cable-ampacity (fetched; standards list, 30-day free trial)
- https://etap.com/product/cable-sizing (fetched; standards list; redirect-ok)
- https://skm.com/cable-ampacity.html (fetched)
- https://www.easypower.com/ (fetched)
- https://www.digsilent.de/en/powerfactory.html (fetched)
- https://www.cyme.com/software/cymcap/ (404, not used)
- https://www.eaton.com/us/en-us/products/utility-grid-solutions/software-modules/power-cable-ampacity-software.html (timeout; search excerpt only)
- https://www.comsol.com/acdc-module (fetched)
- https://ansys.synopsys.com/products/electronics/ansys-maxwell (fetched after redirect from ansys.com)
- https://www.siemens.com/en-us/products/simcenter/electromagnetics-simulation/magnet/ (fetched)
- https://www.siemens.com/en-us/products/simcenter/electromagnetics-simulation/flux/ (fetched)
- https://www.jmag-international.com/ (fetched)
- https://www.femm.info/wiki/HomePage (fetched; no platform or licence stated)
- https://getdp.info/ (fetched)
- https://www.openfoam.com/ (fetched)
- https://pandapower.readthedocs.io/en/latest/ (fetched)
- https://docs.pypsa.org/en/latest/ (fetched; first URL 404)
- https://opendss.epri.com/FaultStudies.html (search excerpt)
- https://opendss.epri.com/BriefHistoryandObjectives.html (search excerpt)
- https://www.mikeholt.com/ (fetched; no ampacity product found)
- https://pdf.archiexpo.com/pdf/mp-husky/cable-bus/149710-264272.html (search excerpt)
- https://www.allumiax.com/blog/neher-mcgrath-study-of-cables-in-power-system (search excerpt)
- https://electricalindustry.ca/latest-articles/a-code-based-approach-to-cable-sizing/ (search excerpt)
- https://www.how2power.com/newsletters/2303/products/H2PToday2303_products_OpenMagnetics.pdf (search excerpt)
- https://github.com/gpitel/PyMKF (search excerpt)
- https://www.vde-verlag.de/proceedings-en/565822103.html (search excerpt)

Opinion sources (forums, dated, not current):
- https://forums.mikeholt.com/threads/skm-easypower-or-etap.96106/latest (search excerpt; mostly 2009 to 2011 posts)
- https://forums.mikeholt.com/threads/skm-etap-easypower-or-edsa.123801/ (search excerpt)

Reddit r/ElectricalEngineering: **not reached**. Searches returned forum threads only.

---

## 8. Open questions

1. **CEC cable ampacity:** Does any tool support CSA C22.1 ampacity? Ask ETAP, SKM, EasyPower, and Eaton (CYMCAP) directly in writing.
2. **CYMCAP details:** Eaton pages failed to load. Obtain the spec sheet and pricing from Eaton.
3. **Paladin, Design Master, ElecCalc, Trimble ProDesign, Schneider Ecodial, Southwire, Mike Holt calculators:** not verified. Need vendor pages retried or contact.
4. **Busbar short-circuit bracing (electrodynamic forces):** no tool in this research covers mechanical bracing. Needs a structural FEA check (for example Ansys Mechanical, Abaqus, or a hand calculation to IEEE/ANSI C37 or IEC 60865). Not researched.
5. **Cable bus temperature rise:** the MP Husky ampacity basis is known, but the calculator and NEC article numbers (368 vs 370) need checking against the current NFPA 70 text.
6. **Transformer design:** Elecsys claim unverified. Commercial transformer design packages used by OEMs (for example in-house systems, or Infolytica MagNet) need vendor contact.
7. **Siemens and Altair:** the link between Altair Flux and Simcenter Flux is unconfirmed. Check with Siemens sales.
8. **Ansys ownership:** the Ansys site redirects to Synopsys (verified). An earlier search excerpt stated "Siemens acquired Ansys", which is not supported.
9. **Linux support:** confirm platform support for COMSOL, Ansys AEDT, Simcenter, and EasyPower (Windows only per vendor).
10. **Reddit opinions:** r/ElectricalEngineering was not reached. Retry with narrower queries if needed.
11. **Search quota:** several searches were rate-limited (too_many_requests). Items marked UNVERIFIED should be re-run when the quota resets.
