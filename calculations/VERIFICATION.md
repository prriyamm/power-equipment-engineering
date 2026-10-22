# Data verification and engineer sign-off

Every code table in `pecalc/data/` has a `_meta.status`: `VERIFIED`, `UNVERIFIED` or `PLACEHOLDER`. Only a qualified engineer who has checked the table against a licensed copy of the code sets `VERIFIED`. This file records each check, so that a reviewer can see what was checked, against what, and by whom.

## How to sign off a table

1. Open your licensed copy of the code at the pages listed below. Do not use this software, a reprint or a website as the source.
2. Check every value in the JSON file against the printed table, row by row.
3. Complete the "Engineer check" columns below and commit the change with your name in the commit message.
4. In the JSON `_meta`, set `"status": "VERIFIED"` and add `"verified_by"` (name) and `"verified_on"` (date). Keep the `pdf_check` record.

If you find a value that does not agree, correct it in the JSON, add a reference test in `tests/` with the printed value and page, and record the change in the table below.

## Pre-check against a PDF (not a sign-off)

On 2026-10-22 an AI assistant (Claude) compared the NEC data with page images of an NFPA 70-2023 PDF. The tables were read from the page images, not from the PDF text layer, because the PDF is a scan. The result is recorded in each file's `_meta.pdf_check`. This narrows what an engineer must look at. It is **not** a verification, and the status of every table stays `UNVERIFIED`.

Result: one value was wrong and is fixed.

| File | Table | Value | Before | Printed (NFPA 70-2023) | Page |
|---|---|---|---:|---:|---|
| `ampacity_nec.json` | Table 310.16 | 8 AWG Al, 60 °C | 30 A | 35 A | 70-187 |

The 30 A value came from an earlier change that followed secondary sources. Those sources follow older editions.

## Sign-off register

| File | Content | Printed pages (NFPA 70-2023) | PDF pre-check (2026-10-22) | Engineer check: name | Date | Result |
|---|---|---|---|---|---|---|
| `ampacity_nec.json` (`raceway`) | Table 310.16, Cu and Al, 14 AWG–2000 kcmil, 60/75/90 °C | 70-187 | Match after the 8 AWG Al fix | | | |
| `ampacity_nec.json` (`free_air`) | Table 310.17, Cu and Al, 14 AWG–2000 kcmil, 60/75/90 °C | 70-188 | Match | | | |
| `reactance_nec_table9.json` | Chapter 9 Table 9, X_L, PVC/aluminum and steel conduit, Ω per 1000 ft | 70-726 | Match | | | |
| `nec_240_4d_small_conductors.json` | 240.4(D)(1), (2), (4)–(8) | 70-122 to 70-123 | Match. 240.4(D)(3), 14 AWG copper-clad aluminum at 10 A, is not in the file | | | |
| `ampacity_cec.json` | CEC Tables 1–4 | (CSA C22.1) | Not checked: `PLACEHOLDER`, contains NEC values | | | |
| `lug_catalog.json` | Manufacturer data | (catalogs) | Not checked: not a code table | | | |
| `dlo_cables.json` | Manufacturer data | (datasheets) | Not checked: not a code table | | | |

Notes for the engineer:

- **Rows not in the files.** Tables 310.16 and 310.17 also list 18 and 16 AWG copper, in the 90 °C column only. Those rows are not in `ampacity_nec.json`, because the feeder sizing module starts at 14 AWG.
- **Conditions not modelled.** The 240.4(D) values for 18 and 16 AWG copper have conditions: continuous-load limits and listed devices. The file does not model them.
- **Clause numbers.** The research notes in `research/` still use 2017 clause numbers in places: 310.15(B)(16) and (B)(17), 310.10(H). The engine code uses 2023 numbering.
