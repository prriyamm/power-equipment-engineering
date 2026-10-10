# Power Equipment Engineering

Open-source engineering platform and research for manufacturers of **transformers, switchgear and cable bus**, including complete transformer + switchgear + cable bus packages, for the US and Canadian markets.

## Goals

1. Build an **ETAP-like engineering platform for equipment manufacturing** (switchgear, transformers, cable bus): general-purpose, not tied to any single project or product rating. See [ARCHITECTURE.md](ARCHITECTURE.md) for layers, principles and roadmap; keep it current when scope changes.
2. Build and keep reliable, traceable calculation methods (sizing, short circuit, ampacity, current sharing, temperature rise, fields, etc.).
3. Keep notes on standards, vendors and decisions.

Never hard-code a product rating (e.g. "15 kV / 2000 A cable bus"); ratings are inputs and specific products are design cases. Shared physics belongs in the engine, not in a product module.

## Layout

- `research/`: software evaluations, vendor comparisons, standards notes. One Markdown file per topic.
- `calculations/`: calculation scripts, spreadsheets and worked examples. State the standard and assumptions at the top of each.
- `notes/`: meeting notes, decisions, open questions.

## Conventions

- Every calculation names the standard it follows (IEEE C57 / C37 / NEC vs IEC 60076 / 62271 / 61439 / 60287) and lists its inputs, assumptions and units.
- Mark which facts were verified from a vendor or standard and which come from memory or need checking.
- Several Claude sessions may work here at once: keep each session to its own files and branch.

## Workflow

- This is an open-source public repo. Work on a branch, open a PR, let CI pass, then merge. Keep PRs focused (one module or fix each).
- Private material (anything from internal notes, customer or product plans, personal paths) never goes in tracked files; it lives in the git-ignored `private/` folder. Maintainers may have extra local instructions in `CLAUDE.local.md`.
- Run `python3 -m unittest discover -s tests` from `calculations/` before every PR.

## Market and priorities

- **Market:** US and Canada. Standards: IEEE / ANSI C37 / C57, NEC (NFPA 70), CEC (CSA C22.1), CSA C22.2 product standards, UL. Not IEC.
- **Priority:** design calculations for manufacturing transformers, switchgear and cable bus, including:
  - cable sizing, ampacity and derating, voltage drop, length and losses;
  - lug selection (type, size, quantity per terminal);
  - magnetic fields around busbars and cable bus;
  - transformer and busbar sizing, temperature rise, short-circuit withstand.
- Calculations are built from the published standards themselves, not from copying commercial software.
