"""SVG cross-section drawings (cable bus) shared by the reports and the desktop app."""

from __future__ import annotations

from html import escape

PHASE_FILL = {"A": "#d64545", "B": "#2f6fd6", "C": "#2e9d5b"}
BLOCK_FILL = "#e9b9a1"      # GPO-3 is commonly supplied red / brick coloured
RAIL_FILL = "#8f9aa6"


def _mm_in(v: float) -> str:
    return f"{v:.0f} mm ({v / 25.4:.2f} in)"


def cablebus_svg(inp, result, block_material: str = "GPO-3", block_lip_mm: float = 10.0,
                 width_px: int = 900) -> str:
    """Cross-section of a cable bus: enclosure, support blocks per tier, cables by phase, dimensions.

    inp: CableBusInput (with enclosure_width_mm / enclosure_height_mm for the housing),
    result: CableBusResult from cablebus.analyse.
    """
    rows = result.conductors
    od = result.cable_od_mm
    xs = [c.x_mm for c in rows]
    ys = [c.y_mm for c in rows]
    xc, yc = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w_in = inp.enclosure_width_mm or (max(xs) - min(xs) + 2 * od)
    h_in = inp.enclosure_height_mm or (max(ys) - min(ys) + 2 * od)
    ts, tc = inp.side_thickness_mm, inp.cover_thickness_mm
    # model extents (mm), y up
    x0, x1 = xc - w_in / 2 - ts, xc + w_in / 2 + ts
    y0, y1 = yc - h_in / 2 - tc, yc + h_in / 2 + tc
    pad_l, pad_r, pad_t, pad_b = 40, 140, 70, 80
    scale = (width_px - pad_l - pad_r) / (x1 - x0)
    height_px = int((y1 - y0) * scale + pad_t + pad_b)

    def X(x):
        return pad_l + (x - x0) * scale

    def Y(y):
        return pad_t + (y1 - y) * scale

    s = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width_px} {height_px}' width='{width_px}' "
         f"height='{height_px}' font-family='Helvetica, Arial, sans-serif' font-size='12'>",
         f"<rect x='0' y='0' width='{width_px}' height='{height_px}' fill='#ffffff'/>"]
    # covers (dashed when not electrically continuous / ventilated)
    dash = "" if inp.covers_continuous else " stroke-dasharray='8 5'"
    for yy in (yc + h_in / 2 + tc / 2, yc - h_in / 2 - tc / 2):
        s.append(f"<line x1='{X(xc - w_in / 2):.1f}' y1='{Y(yy):.1f}' x2='{X(xc + w_in / 2):.1f}' y2='{Y(yy):.1f}' "
                 f"stroke='{RAIL_FILL}' stroke-width='{max(2, tc * scale):.1f}'{dash}/>")
    # side rails
    for xl in (xc - w_in / 2 - ts, xc + w_in / 2):
        s.append(f"<rect x='{X(xl):.1f}' y='{Y(yc + h_in / 2 + tc):.1f}' width='{max(3, ts * scale):.1f}' "
                 f"height='{(h_in + 2 * tc) * scale:.1f}' fill='{RAIL_FILL}'/>")
    # support blocks, one per tier
    tiers = sorted(set(round(y, 3) for y in ys))
    for ty in tiers:
        bh = od + 2 * block_lip_mm
        s.append(f"<rect x='{X(xc - w_in / 2):.1f}' y='{Y(ty + bh / 2):.1f}' width='{w_in * scale:.1f}' "
                 f"height='{bh * scale:.1f}' fill='{BLOCK_FILL}' stroke='#a8664a' stroke-width='1' rx='3'/>")
    # cables
    for c in rows:
        cx, cy, r = X(c.x_mm), Y(c.y_mm), od / 2 * scale
        s.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r:.1f}' fill='{PHASE_FILL[c.phase]}' stroke='#222' "
                 f"stroke-width='1'/>")
        s.append(f"<text x='{cx:.1f}' y='{cy + 4:.1f}' text-anchor='middle' fill='#fff' font-weight='bold'>"
                 f"{c.phase}</text>")
    # dimensions
    yd = Y(yc + h_in / 2 + tc) - 22
    s.append(f"<line x1='{X(xc - w_in / 2):.1f}' y1='{yd:.1f}' x2='{X(xc + w_in / 2):.1f}' y2='{yd:.1f}' "
             "stroke='#333' marker-start='url(#a)' marker-end='url(#a)'/>")
    s.append(f"<text x='{X(xc):.1f}' y='{yd - 6:.1f}' text-anchor='middle'>inside width {_mm_in(w_in)}</text>")
    xd = X(xc + w_in / 2 + ts) + 22
    s.append(f"<line x1='{xd:.1f}' y1='{Y(yc + h_in / 2):.1f}' x2='{xd:.1f}' y2='{Y(yc - h_in / 2):.1f}' "
             "stroke='#333' marker-start='url(#a)' marker-end='url(#a)'/>")
    s.append(f"<text x='{xd + 8:.1f}' y='{Y(yc) - 4:.1f}'>inside height</text>")
    s.append(f"<text x='{xd + 8:.1f}' y='{Y(yc) + 12:.1f}'>{_mm_in(h_in)}</text>")
    # Pitch dimension on the lowest tier with two cables (a Figure 3 trefoil has one cable on top).
    tier_rows = [sorted((c for c in rows if abs(c.y_mm - ty) < 1e-3), key=lambda c: c.x_mm) for ty in tiers]
    tier_rows = [t for t in tier_rows if len(t) > 1]
    if tier_rows:
        a, b = tier_rows[0][:2]
        yb = Y(a.y_mm) + od / 2 * scale + 18 + (block_lip_mm * scale)
        s.append(f"<line x1='{X(a.x_mm):.1f}' y1='{yb:.1f}' x2='{X(b.x_mm):.1f}' y2='{yb:.1f}' stroke='#333' "
                 "marker-start='url(#a)' marker-end='url(#a)'/>")
        s.append(f"<text x='{(X(a.x_mm) + X(b.x_mm)) / 2:.1f}' y='{yb + 15:.1f}' text-anchor='middle'>"
                 f"pitch {b.x_mm - a.x_mm:.0f} mm</text>")
    # legend (bottom row) and title
    ly = height_px - 22
    items = [("circle", PHASE_FILL[p], f"Phase {p}") for p in "ABC"] + [
        ("rect", BLOCK_FILL, f"{block_material} support block"), ("rect", RAIL_FILL, "Al side rail / cover")]
    lx = pad_l
    for kind, col, text in items:
        if kind == "circle":
            s.append(f"<circle cx='{lx + 7}' cy='{ly - 4}' r='7' fill='{col}'/>")
        else:
            s.append(f"<rect x='{lx}' y='{ly - 10}' width='14' height='11' fill='{col}' stroke='#777'/>")
        s.append(f"<text x='{lx + 20}' y='{ly}'>{escape(text)}</text>")
        lx += 30 + 7 * len(text)
    # A library cable carries its own size label (e.g. "444.4 kcmil"); building-wire sizes keep the bare size.
    size = result.cable_data["size_label"] if result.cable_data else result.input.size
    title = (f"{inp.conductors_per_phase} x {size} {inp.material} per phase, "
             f"{inp.tiers} tier(s), pattern {result.pattern}, cable OD {od:.1f} mm")
    s.append(f"<text x='{pad_l}' y='22' font-size='14' font-weight='bold'>{escape(title)}</text>")
    s.append("<defs><marker id='a' viewBox='0 0 10 10' refX='5' refY='5' markerWidth='6' markerHeight='6' "
             "orient='auto-start-reverse'><path d='M0,0 L10,5 L0,10 z' fill='#333'/></marker></defs>")
    s.append("</svg>")
    return "\n".join(s)
