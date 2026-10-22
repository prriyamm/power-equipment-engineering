# Power Equipment Engineering

An open-source, ETAP-style engineering platform for **equipment manufacturers**: switchgear, transformers and cable bus, built for the US and Canadian codes (NEC, CEC / CSA C22.1, IEEE, UL, CSA).

ETAP and similar tools model a power *system*. This project designs and checks the *equipment* that goes into it: conductor sizing, current sharing among paralleled conductors, cable bus layouts at any voltage, shield circulating currents, short-circuit forces, and (on the roadmap) busbar temperature rise, lug selection, transformer design and magnetic fields.

Every result is traceable: it states the formula, inputs, intermediate values and the code clause or standard it comes from, and every data table carries a `VERIFIED` / `UNVERIFIED` / `PLACEHOLDER` status.

## Quick start

Python 3.10+ with no extra packages; works on Windows, macOS and Linux.

```
cd calculations
python3 -m pecalc feeder --voltage 480 --continuous 400 --length 100
python3 -m pecalc cablebus --voltage 600 --current 3000 --size 750 --per-phase 7 --length 200 --fault-ka 65 --xr 20 --fault-time 0.5
python3 -m unittest discover -s tests
```

**Desktop app:** Power Equipment Studio, a native Qt application (Windows installer, Linux, macOS); see [app/README.md](app/README.md) and the Releases page.

See [calculations/README.md](calculations/README.md) for every module and option, and [ARCHITECTURE.md](ARCHITECTURE.md) for the design and roadmap.

## Status

Early development, usable for engineering review. Working and tested (47 reference tests, CI on Linux and Windows):

- **Feeder & cable sizing** (NEC; CEC once its tables are entered) with lug schedule
- **Cable bus** at any voltage: current sharing, table / datasheet / calculated (IEC 60287) ampacity, MV shield circulating currents, aluminum enclosure losses, magnetic field, fault forces
- **Switchgear bus**: Rac/Rdc and lamination sharing, temperature rise, short-circuit bracing
- **Transformer**: preliminary design, losses, impedance (tunable to a target %Z), efficiency incl. DOE test point, fault withstand
- **Lug selection**, design case files and printable calculation packages
- **Desktop app** (Power Equipment Studio) with Windows installer, Linux and macOS builds

**Code-table values were entered from memory and are marked UNVERIFIED**; CEC tables are placeholders and are refused until real values are entered. Every report flags UNVERIFIED data. Check the data against your licensed copies of the codes before relying on any result. [calculations/VERIFICATION.md](calculations/VERIFICATION.md) records what has been checked and is the sign-off sheet for engineers; the NEC tables were pre-checked against the NFPA 70-2023 pages (not a sign-off; status stays UNVERIFIED).

## Important

This software is an engineering aid, not a substitute for a qualified engineer. Results must be reviewed and approved by a licensed professional engineer before use in any design, certification or construction. See the [LICENSE](LICENSE) (no warranty).

## Contributing

Issues and pull requests are welcome, especially verified code-table data, worked examples from standards, and manufacturer test data for validation. Keep each PR focused, include tests with a named reference, and run the test suite first.
