# Engineering Software Landscape

First pass, from general industry knowledge (not yet checked against current vendor pages, pricing or module lists).

## System studies (short circuit, coordination, arc flash, load flow, cable sizing)

| Software | Best for | Notes |
|---|---|---|
| ETAP | Best all-rounder | Industry standard; IEEE/ANSI and IEC; modular, expensive. |
| SKM PowerTools | North American consulting and industrial | Strong coordination and arc flash; cheaper than ETAP. |
| EasyPower | Ease of use | Fast, intuitive; popular with contractors and smaller teams. |
| DIgSILENT PowerFactory | Utility grids, renewables, IEC markets | Strong dynamics; less common at plant level. |
| CYME (Eaton) | Distribution utilities | CYMCAP is the reference for cable ampacity (Neher-McGrath, IEC 60287). |

## Product design

- **Transformers:** in-house design programs plus FEA: Ansys Maxwell, Simcenter MAGNET, COMSOL; FEMM (free).
- **Switchgear:** Ansys / COMSOL for temperature rise, dielectric clearance and short-circuit forces. LV assemblies: Siemens SIMARIS, ABB e-Design, Schneider Ecodial (IEC 61439).
- **Cable bus:** ampacity via CYMCAP, ETAP Cable Ampacity or a validated in-house sheet; US: NEC Article 370.

## Preliminary recommendation

- Complete packages: ETAP (or SKM / EasyPower for a North American, budget-conscious focus).
- Hardware design: add Ansys Maxwell or Simcenter MAGNET.

## Next steps

- [ ] Confirm target market and standards.
- [ ] Verify current pricing, licensing and modules with vendors.
- [ ] Shortlist 2–3 tools and request trials.
