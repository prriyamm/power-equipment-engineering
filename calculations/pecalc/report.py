"""Printable calculation package (self-contained HTML; print to PDF from a browser).

Sections: header (project, revision, date, engine version and commit, input
hash), result banner, data-status warnings, inputs, results, checks with code
clauses, notes, and a sign-off block for the engineer of record.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import html
import subprocess
from pathlib import Path

from . import __version__
from .cases import Case


def _esc(v) -> str:
    return html.escape(str(v))


def _table(rows: list[list], head: list[str] | None = None) -> str:
    out = ["<table>"]
    if head:
        out.append("<tr>" + "".join(f"<th>{_esc(h)}</th>" for h in head) + "</tr>")
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in r) + "</tr>")
    out.append("</table>")
    return "".join(out)


def _kv(d: dict) -> str:
    rows = []
    for k, v in d.items():
        if isinstance(v, dict):
            v = ", ".join(f"{a}: {b}" for a, b in v.items())
        rows.append([k.replace("_", " "), v])
    return _table(rows)


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).parent,
                              capture_output=True, text=True, timeout=5).stdout.strip() or "n/a"
    except (OSError, subprocess.SubprocessError):
        return "n/a"


def _checks(checks: list) -> tuple[str, bool]:
    rows, ok = [], True
    for c in checks:
        c = dataclasses.asdict(c) if dataclasses.is_dataclass(c) else c
        ok &= c["passed"]
        rows.append([("PASS" if c["passed"] else "FAIL"), c["name"], f"{c['value']} {c['unit']}",
                     f"{c['limit']} {c['unit']}", c["clause"], c.get("note", "")])
    return _table(rows, ["", "Check", "Value", "Limit", "Basis", "Note"]), ok


def _sections(module: str, r) -> list[tuple[str, str]]:
    """Module-specific result sections."""
    s: list[tuple[str, str]] = []
    if module == "feeder":
        o = r.recommended
        if o:
            s.append(("Recommended conductors", _kv({
                "conductors": f"{o.sets} set(s) of {o.size_label} per phase",
                "allowable ampacity per set (A)": o.ampacity_per_set_a, "voltage drop (%)": o.vd_pct,
                "voltage drop (V)": o.vd_v, "losses (W)": o.loss_w, "R (ohm/km)": o.r_ohm_per_km,
                "X (ohm/km)": o.x_ohm_per_km})))
        if r.alternatives:
            s.append(("Alternatives (all pass)", _table(
                [[f"{a.sets} x {a.size_label}", a.vd_pct, a.loss_w, a.total_area_mm2] for a in r.alternatives],
                ["Conductors", "VD %", "Loss W", "Copper mm2/phase"])))
        if r.lugs:
            s.append(("Lugs (one end)", _table([[l.quantity, l.conductor, l.style, l.lug_material, l.stud_in,
                                                l.hole_spacing_in or ""] for l in r.lugs.lines],
                                              ["Qty", "Conductor", "Style", "Material", "Stud (in)", "Centres (in)"])))
    elif module == "cablebus":
        s.append(("Summary", _kv({
            "phase pattern": r.pattern, "ampacity basis (worst conductor)": r.ampacity_basis,
            "worst conductor loading (%)": r.max_loading_pct, "voltage drop (%)": r.vd_pct,
            "conductor loss (W)": r.conductor_loss_w, "shield loss (W)": r.shield_loss_w,
            "enclosure loss (W)": r.enclosure_loss_w, "max shield current (A)": r.shield_current_a,
            "magnetic field (uT)": r.field_ut, "fault force (N/m)": r.fault_force_n_per_m,
            "support load (lbf)": r.support_load_lbf})))
        s.append(("Conductor currents", _table(
            [[c.phase, c.tier, c.x_mm, c.current_a, c.share_pct, c.ampacity_a, c.loading_pct] for c in r.conductors],
            ["Phase", "Tier", "x (mm)", "Current (A)", "% of equal share", "Ampacity (A)", "Loading %"])))
        if len(r.patterns_compared) > 1:
            s.append(("Phase patterns compared", _table(
                [[p.pattern, p.max_share_pct, p.loss_w_per_m] for p in r.patterns_compared],
                ["Pattern", "Worst share %", "Loss W/m"])))
    elif module == "bus":
        s.append(("Summary", _kv({
            "temperature rise (C)": r.rise_c, "rating at allowable rise (A)": r.rated_current_at_limit_a,
            "Rac/Rdc": r.rac_over_rdc, "loss per phase (W/m)": r.loss_w_per_m_per_phase,
            "lamination currents (% of equal share)": r.lamination_share_pct,
            "peak fault force (N/m)": r.peak_force_n_per_m, "bending stress (MPa)": r.bending_stress_mpa,
            "support load (N)": r.support_load_n, "max span (m)": r.max_span_m})))
    elif module == "transformer":
        for title, d in (("Design", r.design), ("Losses", r.losses), ("Impedance", r.impedance),
                         ("Performance", r.performance), ("Short circuit", r.short_circuit)):
            s.append((title, _kv(d)))
    elif module == "lugs":
        s.append(("Lug schedule", _table(
            [[l.quantity, l.terminal, l.conductor, l.style, l.lug_material, l.stud_in, l.hole_spacing_in or "",
              l.part_no or "", l.die or "", l.torque or "manufacturer value"] for l in r.lines],
            ["Qty", "Terminal", "Conductor", "Style", "Material", "Stud", "Centres", "Part", "Die", "Torque"])))
        s.append(("Termination temperature", _kv({"rating (C)": r.terminal_temp_c, "basis": r.terminal_temp_basis})))
    return s


def _all_checks(module: str, r) -> list:
    if module == "feeder":
        return list(r.recommended.checks) if r.recommended else []
    return list(r.checks)


CSS = """
body{font:13px/1.45 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1a1a1a;background:#fff;
max-width:960px;margin:24px auto;padding:0 16px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:22px 0 6px;border-bottom:1px solid #ccc;padding-bottom:3px}
table{border-collapse:collapse;width:100%;margin:4px 0}th,td{border:1px solid #d0d0d0;padding:4px 6px;
text-align:left;vertical-align:top}th{background:#f2f2f2}
.banner{padding:8px 12px;border-radius:4px;font-weight:600;margin:12px 0}.pass{background:#e6f4ea;color:#14532d}
.fail{background:#fde8e8;color:#7f1d1d}.warn{background:#fff7e0;color:#6b4e00;font-weight:400}
.sign td{height:42px}.small{color:#555;font-size:11px}
@media print{body{margin:0}h2{break-after:avoid}table{break-inside:auto}tr{break-inside:avoid}}
"""


def render(case: Case, result, results_first: bool = False) -> str:
    module = case.module
    checks_html, ok = _checks(_all_checks(module, result))
    ok = ok and bool(getattr(result, "passed", True)) and not (module == "feeder" and not result.recommended)
    notes = list(getattr(result, "notes", []))
    if module == "feeder" and result.lugs:
        notes += result.lugs.notes
    flagged = sorted({w for n in notes + [checks_html] for w in ("UNVERIFIED", "PLACEHOLDER") if w in n})
    inputs = dataclasses.asdict(case.input_object())
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,"
        f"initial-scale=1'><title>{_esc(case.title or module)} - calculation</title><style>{CSS}</style></head><body>",
        f"<h1>{_esc(case.title or module.title())}</h1>",
        _table([["Project", case.project or "-", "Revision", case.revision or "-"],
                ["Module", module, "Date", now],
                ["Engine", f"pecalc {__version__} ({_commit()})", "Input hash", case.input_hash()]]),
        f"<div class='banner {'pass' if ok else 'fail'}'>RESULT: {'PASS' if ok else 'FAIL'} - "
        f"{sum(1 for c in _all_checks(module, result))} checks</div>",
    ]
    if flagged:
        parts.append("<div class='banner warn'>This calculation uses data or methods marked "
                     f"{' / '.join(flagged)}. Verify them against the licensed code or standard before "
                     "relying on the result.</div>")
    body = [f"<h2>{_esc(title)}</h2>{html_}" for title, html_ in _sections(module, result)]
    body.append("<h2>Checks</h2>" + checks_html)
    if notes:
        body.append("<h2>Notes</h2><ul>" + "".join(f"<li>{_esc(n)}</li>" for n in notes) + "</ul>")
    inputs_html = "<h2>Inputs</h2>" + _kv(inputs)
    parts += (body + [inputs_html]) if results_first else ([inputs_html] + body)
    parts.append("<h2>Sign-off</h2>" + "<table class='sign'><tr><th>Prepared by</th><th>Checked by</th>"
                 "<th>Approved (P.Eng. / PE seal)</th></tr><tr><td></td><td></td><td></td></tr>"
                 "<tr><td>Date:</td><td>Date:</td><td>Date:</td></tr></table>")
    parts.append("<p class='small'>Generated by pecalc, an engineering aid. Results must be reviewed and approved by "
                 "a licensed professional engineer before use in design, certification or construction.</p>")
    parts.append("</body></html>")
    return "\n".join(parts)


def write_report(case: Case, result, path: str | Path) -> Path:
    p = Path(path)
    p.write_text(render(case, result), encoding="utf-8")
    return p
