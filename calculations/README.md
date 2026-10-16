# pecalc: power equipment engineering calculations

The calculation engine of the platform described in [../ARCHITECTURE.md](../ARCHITECTURE.md). Plain Python 3.10+, no extra packages; runs the same on Windows and Linux. If numpy is installed it is used automatically to speed up large solves.

## Run

From this folder (`calculations/`):

```
python3 -m pecalc feeder --voltage 480 --continuous 400 --length 100
python3 -m pecalc cablebus --voltage 600 --current 3000 --size 750 --per-phase 4 --length 200 --fault-ka 65 --xr 20
python3 -m pecalc cablebus-design --voltage 15000 --current 2000 --length 200 --insulation EPR --insulation-mm 7.2 \
    --shield-mm 0.13 --jacket-mm 2 --fault-ka 40 --choose 3 --report cablebus-option3.html
python3 -m pecalc transformer --load-kva 1180 --growth 1.25 --hv 13800 --lv 480 --target-z 5.75 --tune --doe-eff 99.48
python3 -m pecalc bus --current 3000 --thickness 6.35 --width 152.4 --bars 3 --phase-spacing 200 --orientation edge_to_edge --fault-ka 65 --air-rise 15
python3 -m pecalc cablebus --voltage 15000 --current 2000 --size 750 --per-phase 3 --insulation EPR \
    --insulation-mm 7.2 --shield-mm 0.13 --jacket-mm 2 --shield-bonding both_ends --length 200 --fault-ka 40
```

On Windows use `py -m pecalc ...`. Add `--json` for machine-readable output, `--help` for every option. Lengths default to feet (`--length-unit m` for metres).

## Design cases and reports

Save inputs as a case file (see `../examples/`), then run it or produce a printable calculation package:

```
python3 -m pecalc run ../examples/cablebus-15kv-2000a.json
python3 -m pecalc run ../examples/cablebus-15kv-2000a.json --report cablebus-calc.html
```

The report includes inputs, results, checks with code clauses, data-status warnings, the engine version and an input hash, and a Prepared / Checked / Approved block. Open it in a browser and print to PDF.

## Test

```
python3 -m unittest discover -s tests -v
```

## Modules

| File | What it does |
|---|---|
| `conductors.py` | sizes, geometry, DC/AC resistance (resistivity + temperature, IEC 60287 skin/proximity), GMR, reactance |
| `ampacity.py` | NEC / CEC tables (status-flagged data), ambient and grouping correction, clause references |
| `sizing.py` | feeder sizing: parallel sets, terminal (110.14(C), always Table 310.16) and continuous-load rules, NEC 240.4(D) small-conductor limits, voltage drop, losses, short-circuit withstand |
| `reactance_derived.py` | NEC Table 9 reactance plus DERIVED rows for 700/800/900 and 1250–2000 kcmil (ln-kcmil interpolation/extrapolation, touching-trefoil floor); flagged in results |
| `validate.py` | shared input checks (voltage, power factor, clearing time, X/R) raising `ValueError` |
| `impedance.py` | multi-conductor impedance (Carson), current sharing among paralleled conductors, bonded shield circulating currents, open-circuit (single-point bonded) shield voltages |
| `forces.py` | time-domain short-circuit forces on any conductor layout (worst case over inception angle) |
| `thermal.py` | calculated ampacity: IEC 60287 / Neher-McGrath thermal model for cables in free air, dielectric loss, shield loss factor |
| `lugs.py` | lug style, material, stud and hole pattern, quantity per termination, pad capacity, NEC 110.14(C) / CEC 4-006 terminal temperature; part/die/torque from `data/lug_catalog.json` |
| `switchgear.py` | switchgear / switchboard bus: filament model for Rac/Rdc and lamination sharing, temperature rise (convection + radiation), short-circuit force per phase pack, bar bending stress, support load and max span |
| `transformer.py` | 3-phase core-type preliminary design (EMF / output equations), losses, Rogowski impedance with tuning to a target %Z, efficiency incl. DOE test point, regulation, secondary fault current, 2 s thermal withstand, outer-winding hoop stress, standard kVA selection |
| `cablebus_design.py` | cable bus **designer**: enumerates size x conductors per phase x 1/2/3 tiers, code spacing, smallest standard enclosure, full analysis of each, GPO-3 support-block check, ranked options (least copper / smallest enclosure / most margin) |
| `drawing.py` | SVG cross-section drawings (enclosure, support blocks, cables by phase, dimensions) used by reports and the app |
| `field.py` | magnetic flux density (2-D Biot-Savart, RMS resultant) around any conductor set; ICNIRP reference levels |
| `cablebus.py` | cable bus design check, any voltage: layout, phase pattern search, sharing, ampacity (table / datasheet / calculated per cable), VD, losses, shield losses, single-point shield standing voltage (normal and through-fault, per bonded section, user-set limit) with a single-point vs both-ends bonding comparison, aluminum enclosure induced currents and loss, magnetic field, fault forces |

## Data status

| File | Status | Action needed |
|---|---|---|
| `data/ampacity_nec.json` | UNVERIFIED | Check Tables 310.16 / 310.17 against NFPA 70-2023, then set `VERIFIED` with name and date |
| `data/ampacity_cec.json` | PLACEHOLDER (copy of NEC values) | Enter CSA C22.1 Tables 1–4; CEC is refused until then |
| `data/reactance_nec_table9.json` | UNVERIFIED | Check against NEC Chapter 9 Table 9 |
| `data/nec_240_4d_small_conductors.json` | UNVERIFIED (from memory, NEC 2023) | Check NEC 240.4(D) |
| `reactance_derived.py` (computed) | DERIVED — UNVERIFIED | Not a published value; replace with manufacturer data where available |

CEC spot values gathered during research (unverified; confirm against CSA C22.1), to test against once the tables are entered: 750 kcmil Cu Table 1 90 °C = 805 A, 75 °C = 691 A; 1000 kcmil Cu Table 1 90 °C = 960 A, 75 °C = 823 A; 750 kcmil Cu Table 2 75 °C = 418 A; 750 / 1000 kcmil Al Table 4 75 °C = 339 / 392 A.

## Not yet included

MV code tables, transverse eddy losses in the enclosure, wire bending space, overcurrent device coordination, solar radiation and cable-in-tray/conduit thermal models.

## Calculated ampacity note

The IEC 60287 model gives 17–28 % more ampacity than NEC Table 310.17 for isolated 600 V cables, consistent with the NEC tables being conservative. Code tables therefore remain the default for code-compliance checks at 2000 V and below; the calculated method is used above 2000 V or when chosen explicitly, and is permitted by NEC 310.14(B) / 315.60(B) under engineering supervision.
