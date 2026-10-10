# pecalc: power equipment engineering calculations

The calculation engine of the platform described in [../ARCHITECTURE.md](../ARCHITECTURE.md). Plain Python 3.10+, no extra packages; runs the same on Windows and Linux.

## Run

From this folder (`calculations/`):

```
python3 -m pecalc feeder --voltage 480 --continuous 400 --length 100
python3 -m pecalc cablebus --voltage 600 --current 3000 --size 750 --per-phase 4 --length 200 --fault-ka 65 --xr 20
python3 -m pecalc cablebus --voltage 15000 --current 2000 --size 750 --per-phase 3 --insulation EPR \
    --insulation-mm 7.2 --shield-mm 0.13 --jacket-mm 2 --shield-bonding both_ends --length 200 --fault-ka 40
```

On Windows use `py -m pecalc ...`. Add `--json` for machine-readable output, `--help` for every option. Lengths default to feet (`--length-unit m` for metres).

## Test

```
python3 -m unittest discover -s tests -v
```

## Modules

| File | What it does |
|---|---|
| `conductors.py` | sizes, geometry, DC/AC resistance (resistivity + temperature, IEC 60287 skin/proximity), GMR, reactance |
| `ampacity.py` | NEC / CEC tables (status-flagged data), ambient and grouping correction, clause references |
| `sizing.py` | feeder sizing: parallel sets, terminal and continuous-load rules, voltage drop, losses, short-circuit withstand |
| `impedance.py` | multi-conductor impedance (Carson), current sharing among paralleled conductors, bonded shield circulating currents |
| `forces.py` | time-domain short-circuit forces on any conductor layout (worst case over inception angle) |
| `thermal.py` | calculated ampacity: IEC 60287 / Neher-McGrath thermal model for cables in free air, dielectric loss, shield loss factor |
| `cablebus.py` | cable bus design check, any voltage: layout, phase pattern search, sharing, ampacity (table / datasheet / calculated per cable), VD, losses, shield losses, fault forces |

## Data status

| File | Status | Action needed |
|---|---|---|
| `data/ampacity_nec.json` | UNVERIFIED | Check Tables 310.16 / 310.17 against NFPA 70-2023, then set `VERIFIED` with name and date |
| `data/ampacity_cec.json` | PLACEHOLDER (copy of NEC values) | Enter CSA C22.1 Tables 1–4; CEC is refused until then |
| `data/reactance_nec_table9.json` | UNVERIFIED | Check against NEC Chapter 9 Table 9 |

CEC spot values gathered during research (unverified; confirm against CSA C22.1), to test against once the tables are entered: 750 kcmil Cu Table 1 90 °C = 805 A, 75 °C = 691 A; 1000 kcmil Cu Table 1 90 °C = 960 A, 75 °C = 823 A; 750 kcmil Cu Table 2 75 °C = 418 A; 750 / 1000 kcmil Al Table 4 75 °C = 339 / 392 A.

## Not yet included

MV code tables, enclosure eddy losses, lug selection, overcurrent device coordination, solar radiation and cable-in-tray/conduit thermal models.

## Calculated ampacity note

The IEC 60287 model gives 17–28 % more ampacity than NEC Table 310.17 for isolated 600 V cables, consistent with the NEC tables being conservative. Code tables therefore remain the default for code-compliance checks at 2000 V and below; the calculated method is used above 2000 V or when chosen explicitly, and is permitted by NEC 310.14(B) / 315.60(B) under engineering supervision.
