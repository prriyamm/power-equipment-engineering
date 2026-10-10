# pecalc: power equipment engineering calculations

The calculation engine of the platform described in [../ARCHITECTURE.md](../ARCHITECTURE.md). Plain Python 3.10+, no extra packages; runs the same on Windows and Linux.

## Run

From this folder (`calculations/`):

```
python3 -m pecalc feeder --voltage 480 --continuous 400 --length 100
python3 -m pecalc cablebus --voltage 600 --current 3000 --size 750 --per-phase 4 --length 200 --fault-ka 65 --xr 20
python3 -m pecalc cablebus --voltage 15000 --current 2000 --size 750 --per-phase 3 --od 45 \
    --cable-ampacity 900 --shield-bonding both_ends --shield-area 16 --shield-diameter 38 --length 200 --fault-ka 40
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
| `cablebus.py` | cable bus design check, any voltage: layout, phase pattern search, sharing, ampacity, VD, losses, shield losses, fault forces |

## Data status

| File | Status | Action needed |
|---|---|---|
| `data/ampacity_nec.json` | UNVERIFIED | Check Tables 310.16 / 310.17 against NFPA 70-2023, then set `VERIFIED` with name and date |
| `data/ampacity_cec.json` | PLACEHOLDER (copy of NEC values) | Enter CSA C22.1 Tables 1–4; CEC is refused until then |
| `data/reactance_nec_table9.json` | UNVERIFIED | Check against NEC Chapter 9 Table 9 |

CEC spot values gathered during research (unverified; confirm against CSA C22.1), to test against once the tables are entered: 750 kcmil Cu Table 1 90 °C = 805 A, 75 °C = 691 A; 1000 kcmil Cu Table 1 90 °C = 960 A, 75 °C = 823 A; 750 kcmil Cu Table 2 75 °C = 418 A; 750 / 1000 kcmil Al Table 4 75 °C = 339 / 392 A.

## Not yet included

Calculated (thermal-model) ampacity, MV code tables, enclosure eddy losses, lug selection, overcurrent device coordination.
