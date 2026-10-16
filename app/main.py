"""Power Equipment Studio: desktop application for the pecalc engine.

Run:  python app/main.py      (needs PySide6: pip install -r app/requirements.txt)
"""

from __future__ import annotations

import dataclasses
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "calculations"))


def selftest() -> int:
    """Run every bundled example through the engine and report renderer (checks builds; needs no display)."""
    from pecalc import __version__ as version
    from pecalc.cases import Case
    from pecalc.report import render
    examples = ROOT / "examples"
    ok = True
    for f in sorted(examples.glob("*.json")):
        try:
            case = Case.load(f)
            result = case.run()
            render(case, result)
            print(f"ok    {f.name}: {'PASS' if getattr(result, 'passed', True) else 'FAIL'}")
        except Exception as e:  # report and continue
            ok = False
            print(f"ERROR {f.name}: {e}")
    print(f"pecalc {version}, examples from {examples}")
    return 0 if ok else 1


if __name__ == "__main__" and "--selftest" in sys.argv:
    sys.exit(selftest())

from PySide6.QtCore import QObject, QPointF, QRectF, QRunnable, Qt, QThreadPool, Signal  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QAction, QColor, QFont, QIcon, QKeySequence, QPageLayout, QPageSize, QPainter, QPalette, QPdfWriter, QPen,
    QTextDocument, QImage,
)
from PySide6.QtCore import QByteArray, QMarginsF, QUrl  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402
from PySide6.QtSvgWidgets import QSvgWidget  # noqa: E402
import re  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizePolicy,
    QSplitter, QStackedWidget, QStyleFactory, QTabWidget, QTableWidget, QTableWidgetItem, QTextBrowser, QToolBar,
    QVBoxLayout, QWidget, QAbstractItemView, QHeaderView,
)

from pecalc import __version__  # noqa: E402
from pecalc.cablebus import CableBusInput, analyse  # noqa: E402
from pecalc.cablebus_design import DesignRequest, design_options  # noqa: E402
from pecalc.drawing import cablebus_svg  # noqa: E402
from pecalc.cases import MODULES, Case  # noqa: E402
from pecalc.conductors import SIZES  # noqa: E402
from pecalc.lugs import LugInput  # noqa: E402
from pecalc.report import render  # noqa: E402
from pecalc.sizing import FeederInput  # noqa: E402
from pecalc.switchgear import BusInput  # noqa: E402
from pecalc.transformer import TransformerInput  # noqa: E402

APP_NAME = "Power Equipment Studio"
EXAMPLES = ROOT / "examples"
ICON = ROOT / "app" / "assets" / "icon.png"

# --- form specification -------------------------------------------------------

MODULE_INFO = {
    "feeder": ("Feeder & Cable", FeederInput, "Size feeder conductors: parallel sets, terminations, voltage drop, lugs"),
    "cablebus": ("Cable Bus", CableBusInput, "Cable bus at any voltage: sharing, ampacity, shields, enclosure, field, faults"),
    "bus": ("Switchgear Bus", BusInput, "Switchgear / switchboard bus: temperature rise and short-circuit bracing"),
    "transformer": ("Transformer", TransformerInput, "Preliminary transformer design, losses, impedance, DOE, faults"),
    "lugs": ("Lugs", LugInput, "Lug style, quantity, stud and pad capacity"),
}

MODULE_INFO_DESIGN = ("Cable Bus Designer", DesignRequest,
                      "Recommended cable bus designs: conductors, tiers, phase layout, enclosure size, GPO-3 blocks")

GROUPS = {
    "designer": [
        ("Requirement", ["code", "voltage_v", "current_a", "power_factor", "length_m", "ambient_c", "material"]),
        ("Cable", ["sizes", "insulation", "insulation_mm", "shield_mm", "jacket_mm", "shield_bonding",
                   "ampacity_method", "max_per_phase"]),
        ("Layout & enclosure", ["tier_options", "enclosure_widths_in", "enclosure_heights_in", "edge_clearance_mm",
                                "vertical_clearance_mm", "max_loading_pct"]),
        ("Short circuit & blocks", ["fault_ka", "x_over_r", "support_span_m", "block_material",
                                    "block_thickness_mm", "block_rated_load_n"]),
    ],
    "feeder": [
        ("System", ["code", "voltage_v", "phases", "continuous_a", "noncontinuous_a", "power_factor", "length_m"]),
        ("Conductor", ["material", "insulation_temp_c", "terminal_temp_c", "installation", "conduit",
                       "current_carrying_per_raceway", "ambient_c", "sets", "max_sets", "hundred_percent_rated"]),
        ("Limits & fault", ["max_vd_pct", "fault_ka", "fault_clearing_s"]),
    ],
    "cablebus": [
        ("System", ["code", "voltage_v", "current_a", "power_factor", "length_m", "ambient_c"]),
        ("Conductors", ["material", "size", "conductors_per_phase", "tiers", "pattern", "spacing_mm",
                        "insulation_temp_c", "terminal_temp_c"]),
        ("Ampacity method", ["ampacity_method", "cable_ampacity_a", "cable_od_mm", "insulation", "insulation_mm",
                             "shield_mm", "jacket_mm", "shield_bonding"]),
        ("Enclosure", ["enclosure_width_mm", "enclosure_height_mm", "side_thickness_mm", "covers_continuous",
                       "enclosure_alloy"]),
        ("Short circuit", ["fault_ka", "fault_clearing_s", "x_over_r", "support_span_m"]),
    ],
    "bus": [
        ("Rating", ["standard", "current_a", "voltage_v", "ambient_c", "internal_air_rise_c", "max_rise_c"]),
        ("Bars", ["material", "bar_thickness_mm", "bar_width_mm", "bars_per_phase", "bar_gap_mm",
                  "phase_spacing_mm", "orientation", "finish"]),
        ("Short circuit", ["fault_ka", "x_over_r", "support_span_m", "support_condition", "yield_mpa",
                           "support_rating_n"]),
    ],
    "transformer": [
        ("Rating", ["kva", "hv_v", "lv_v", "hv_connection", "lv_connection", "kind", "conductor", "power_factor"]),
        ("Design", ["b_max_t", "k_et", "j_lv_a_mm2", "j_hv_a_mm2", "window_ratio", "target_z_pct"]),
        ("Compliance & fault", ["bil_kv", "doe_date", "doe_submersible", "doe_min_efficiency_pct", "source_mva", "source_x_over_r", "fault_duration_s", "conductor_proof_mpa"]),
    ],
    "lugs": [
        ("Circuit", ["code", "size", "material", "sets_per_phase", "phases", "circuit_current_a",
                     "equipment_terminal_temp_c"]),
        ("Termination", ["termination", "pad_positions", "pad_two_sided", "neutral", "neutral_size", "ground_size"]),
    ],
}

CHOICES = {
    "code": ["NEC", "CEC"], "material": ["Cu", "Al"], "conductor": ["Cu", "Al"],
    "installation": ["raceway", "free_air"], "conduit": ["pvc", "aluminum", "steel"],
    "insulation": ["XLPE", "EPR", "PVC", "XHHW", "RW90"], "jacket": ["PVC", "PE"],
    "shield_bonding": ["none", "single_point", "both_ends"],
    "ampacity_method": ["auto", "table", "datasheet", "calculated"],
    "enclosure_alloy": ["6063-T6", "6061-T6", "1350"], "orientation": ["face_to_face", "edge_to_edge"],
    "finish": ["tin", "bare", "silver", "painted"], "support_condition": ["continuous", "pinned", "fixed"],
    "kind": ["liquid", "dry"], "hv_connection": ["delta", "wye"], "lv_connection": ["wye", "delta"],
    "termination": ["bus", "stud", "breaker"], "size": list(SIZES), "neutral_size": [""] + list(SIZES),
    "ground_size": [""] + list(SIZES), "insulation_temp_c": ["90", "75", "60"],
    "terminal_temp_c": ["", "75", "60", "90"], "equipment_terminal_temp_c": ["", "75", "60", "90"],
    "phases": ["3", "1"], "block_material": ["GPO-3", "GPO-2", "GPO-1"],
}

UNITS = (("_mm2", "mm²"), ("_a_mm2", "A/mm²"), ("_mm", "mm"), ("_m", "m"), ("_ka", "kA"), ("_a", "A"),
         ("_v", "V"), ("_c", "°C"), ("_pct", "%"), ("_hz", "Hz"), ("_mpa", "MPa"), ("_n", "N"), ("_s", "s"),
         ("_t", "T"), ("_mva", "MVA"))
LABELS = {"kva": ("Rating", "kVA"), "bil_kv": ("HV winding BIL (DOE, MV dry)", "kV"),
          "doe_date": ("DOE manufacture date (YYYY-MM-DD, blank = today)", ""),
          "doe_submersible": ("DOE submersible (liquid)", ""), "x_over_r": ("X/R ratio", ""), "source_x_over_r": ("Source X/R ratio", ""), "k_et": ("Et constant K", ""),
          "hv_v": ("HV line voltage", "V"), "lv_v": ("LV line voltage", "V"), "power_factor": ("Power factor", ""),
          "current_carrying_per_raceway": ("Current-carrying conductors per raceway", ""),
          "hundred_percent_rated": ("Equipment rated 100 % continuous", ""), "sets": ("Parallel sets (blank = auto)", ""),
          "sizes": ("Sizes to try", "kcmil"), "tier_options": ("Tiers to try", ""),
          "enclosure_widths_in": ("Enclosure widths", "in"), "enclosure_heights_in": ("Enclosure heights", "in"),
          "max_loading_pct": ("Max cable loading", "%"), "block_rated_load_n": ("Tested block rating", "N"),
          "block_thickness_mm": ("Block thickness", "mm")}


def label_for(name: str) -> tuple[str, str]:
    if name in LABELS:
        return LABELS[name]
    for suffix, unit in sorted(UNITS, key=lambda u: -len(u[0])):
        if name.endswith(suffix):
            base = name[: -len(suffix)]
            return base.replace("_", " ").capitalize(), unit
    return name.replace("_", " ").capitalize(), ""


def parse_type(t: str) -> tuple[str, bool]:
    t = str(t).replace(" ", "")
    optional = "None" in t
    for base in ("bool", "int", "float", "tuple", "str"):
        if t.startswith(base) or f"|{base}" in t or t.startswith(f"{base}|"):
            return base, optional
    return "str", optional


# --- form widget ---------------------------------------------------------------

class InputForm(QScrollArea):
    def __init__(self, module: str):
        super().__init__()
        self.module = module
        self.cls = MODULE_INFO_DESIGN[1] if module == "designer" else MODULE_INFO[module][1]
        self.fields = {f.name: f for f in dataclasses.fields(self.cls)}
        self.widgets: dict[str, QWidget] = {}
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(4, 4, 8, 4)
        used = set()
        for title, names in GROUPS[module]:
            lay.addWidget(self._group(title, names))
            used |= set(names)
        rest = [n for n in self.fields if n not in used]
        if rest:
            adv = self._group("Advanced", rest)
            adv.setCheckable(True)
            adv.setChecked(False)
            for w in adv.findChildren(QWidget):
                w.setVisible(False)
            adv.toggled.connect(lambda on, g=adv: [w.setVisible(on) for w in g.findChildren(QWidget)])
            lay.addWidget(adv)
        lay.addStretch(1)
        self.setWidget(body)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.set_values({})

    def _group(self, title: str, names: list[str]) -> QGroupBox:
        box = QGroupBox(title)
        form = QFormLayout(box)
        form.setLabelAlignment(Qt.AlignRight)
        for n in names:
            f = self.fields[n]
            kind, optional = parse_type(f.type)
            text, unit = label_for(n)
            if kind == "bool":
                w = QCheckBox()
            elif n in CHOICES:
                w = QComboBox()
                w.addItems([c or "auto" for c in CHOICES[n]])
            else:
                w = QLineEdit()
                if optional:
                    w.setPlaceholderText("auto / not used")
            w.setToolTip(n)
            self.widgets[n] = w
            form.addRow(f"{text}{f' ({unit})' if unit else ''}", w)
        return box

    def set_values(self, values: dict) -> None:
        defaults = {n: (f.default if f.default is not dataclasses.MISSING else None) for n, f in self.fields.items()}
        defaults.update(values)
        for n, w in self.widgets.items():
            v = defaults.get(n)
            if isinstance(w, QCheckBox):
                w.setChecked(bool(v))
            elif isinstance(w, QComboBox):
                txt = "auto" if v in (None, "") else str(v)
                i = w.findText(txt)
                if i < 0:
                    w.addItem(txt)
                    i = w.findText(txt)
                w.setCurrentIndex(i)
            else:
                if isinstance(v, (tuple, list)):
                    v = ", ".join(f"{x:g}" if isinstance(x, float) else str(x) for x in v)
                w.setText("" if v is None else (f"{v:g}" if isinstance(v, float) else str(v)))

    def values(self) -> dict:
        out = {}
        for n, w in self.widgets.items():
            kind, optional = parse_type(self.fields[n].type)
            if isinstance(w, QCheckBox):
                out[n] = w.isChecked()
                continue
            raw = (w.currentText() if isinstance(w, QComboBox) else w.text()).strip()
            if raw in ("", "auto") and (optional or n in ("pattern", "ampacity_method")):
                if n in ("pattern", "ampacity_method"):
                    out[n] = "auto"
                elif optional:
                    out[n] = None
                continue
            try:
                if kind == "int":
                    out[n] = int(float(raw))
                elif kind == "float":
                    out[n] = float(raw)
                elif kind == "tuple":
                    conv = str if n == "sizes" else (int if n == "tier_options" else float)
                    out[n] = tuple(conv(x.strip() if conv is str else float(x)) for x in raw.split(",") if x.strip())
                else:
                    out[n] = raw
            except ValueError:
                text, _ = label_for(n)
                raise ValueError(f"'{text}' must be a number (got '{raw}')") from None
        return out


# --- figures in rich text --------------------------------------------------------

_SVG = re.compile(r"<svg\b.*?</svg>", re.S)


def with_figures(doc: QTextDocument, html_doc: str, max_width: int = 720) -> str:
    """Qt rich text cannot draw inline SVG: render each figure to an image resource."""
    def repl(m, counter=[0]):
        counter[0] += 1
        r = QSvgRenderer(QByteArray(m.group(0).encode()))
        size = r.defaultSize()
        img = QImage(size * 2, QImage.Format_ARGB32)
        img.fill(Qt.white)
        p = QPainter(img)
        r.render(p)
        p.end()
        name = f"figure{counter[0]}.png"
        doc.addResource(QTextDocument.ImageResource, QUrl(name), img)
        return f"<img src='{name}' width='{min(max_width, size.width())}'>"
    return _SVG.sub(repl, html_doc)


# --- cross-section drawing ----------------------------------------------------

PHASE_COLOURS = {"A": QColor("#d64545"), "B": QColor("#2f6fd6"), "C": QColor("#2e9d5b")}


class CrossSection(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(220)
        self.shapes: list[tuple] = []   # ("circle", x, y, r, phase, label) or ("rect", x, y, w, h, phase, label)
        self.outline = None             # (x, y, w, h) enclosure
        self.caption = ""

    def show_cablebus(self, inp, result) -> None:
        od = inp.cable_od_mm or (result.layout_height_mm if inp.tiers == 1 else 30)
        self.shapes = [("circle", c.x_mm, c.y_mm, od / 2, c.phase, f"{c.loading_pct:.0f}%") for c in result.conductors]
        self.outline = None
        if inp.enclosure_width_mm:
            xs = [c.x_mm for c in result.conductors]
            ys = [c.y_mm for c in result.conductors]
            xc, yc = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            h = inp.enclosure_height_mm or (max(ys) - min(ys) + 2 * od)
            self.outline = (xc - inp.enclosure_width_mm / 2, yc - h / 2, inp.enclosure_width_mm, h)
        self.caption = f"Pattern {result.pattern}  ·  labels = loading of each cable"
        self.update()

    def show_bus(self, inp, result) -> None:
        t, w, n = inp.bar_thickness_mm, inp.bar_width_mm, inp.bars_per_phase
        gap = inp.bar_gap_mm if inp.bar_gap_mm is not None else t
        pack = n * t + (n - 1) * gap
        self.shapes, self.outline = [], None
        for p, ph in enumerate("ABC"):
            xc = p * inp.phase_spacing_mm
            for b in range(n):
                off = -pack / 2 + b * (t + gap)
                if inp.orientation == "face_to_face":
                    self.shapes.append(("rect", xc + off, -w / 2, t, w, ph, ""))
                else:
                    self.shapes.append(("rect", xc - w / 2, off, w, t, ph, ""))
        self.caption = f"{n} bar(s) per phase · {inp.orientation.replace('_', ' ')} · rise {result.rise_c} °C"
        self.update()

    def clear(self) -> None:
        self.shapes, self.outline, self.caption = [], None, ""
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pal = self.palette()
        p.fillRect(self.rect(), pal.color(QPalette.Base))
        if not self.shapes:
            p.setPen(pal.color(QPalette.PlaceholderText))
            p.drawText(self.rect(), Qt.AlignCenter, "Cross-section appears here after a cable bus or bus run")
            return
        xs, ys = [], []
        for s in self.shapes:
            if s[0] == "circle":
                xs += [s[1] - s[3], s[1] + s[3]]
                ys += [s[2] - s[3], s[2] + s[3]]
            else:
                xs += [s[1], s[1] + s[3]]
                ys += [s[2], s[2] + s[4]]
        if self.outline:
            x, y, w, h = self.outline
            xs += [x, x + w]
            ys += [y, y + h]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        margin = 24
        avail_w, avail_h = self.width() - 2 * margin, self.height() - 2 * margin - 18
        scale = min(avail_w / max(x1 - x0, 1), avail_h / max(y1 - y0, 1))
        ox = margin + (avail_w - (x1 - x0) * scale) / 2
        oy = margin + (avail_h - (y1 - y0) * scale) / 2

        def pt(x, y):  # y up
            return QPointF(ox + (x - x0) * scale, oy + (y1 - y) * scale)
        if self.outline:
            x, y, w, h = self.outline
            p.setPen(QPen(QColor("#9aa7b4"), 3))
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(pt(x, y + h), pt(x + w, y)))
        font = QFont(self.font())
        font.setPointSizeF(max(6.5, min(9.0, scale * 6)))
        p.setFont(font)
        for s in self.shapes:
            col = PHASE_COLOURS[s[-2]]
            p.setPen(QPen(col.darker(140), 1.5))
            fill = QColor(col)
            fill.setAlpha(170)
            p.setBrush(fill)
            if s[0] == "circle":
                c = pt(s[1], s[2])
                r = s[3] * scale
                p.drawEllipse(c, r, r)
                p.setPen(pal.color(QPalette.Text))
                p.drawText(QRectF(c.x() - 30, c.y() + r + 1, 60, 14), Qt.AlignCenter, s[-1])
                p.setPen(Qt.white)
                p.drawText(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), Qt.AlignCenter, s[-2])
            else:
                p.drawRect(QRectF(pt(s[1], s[2] + s[4]), pt(s[1] + s[3], s[2])))
        p.setPen(pal.color(QPalette.Text))
        p.drawText(QRectF(0, self.height() - 22, self.width(), 18), Qt.AlignCenter, self.caption)


# --- background worker --------------------------------------------------------

class _Signals(QObject):
    done = Signal(object, object)
    failed = Signal(str)


class Job(QRunnable):
    def __init__(self, case, fn=None):
        super().__init__()
        self.case = case
        self.fn = fn or (lambda c: c.run())
        self.signals = _Signals()

    def run(self):
        try:
            result = self.fn(self.case)
            self.signals.done.emit(self.case, result)
        except Exception as e:  # report every engine error to the user
            msg = str(e) if isinstance(e, ValueError) else f"{e}\n\n{traceback.format_exc()}"
            self.signals.failed.emit(msg)


# --- module page ---------------------------------------------------------------

class ModulePage(QWidget):
    status = Signal(str)

    def __init__(self, module: str):
        super().__init__()
        self.module = module
        title, _, blurb = MODULE_INFO[module]
        self.form = InputForm(module)
        self.options = {}
        if module == "transformer":
            self.tune = QCheckBox("Tune window to meet target impedance")
            self.tune.setChecked(True)

        head = QLabel(f"<b style='font-size:15pt'>{title}</b><br><span>{blurb}</span>")
        head.setTextFormat(Qt.RichText)
        self.run_btn = QPushButton("Run calculation")
        self.run_btn.setObjectName("primary")
        self.run_btn.setShortcut(QKeySequence("Ctrl+R"))
        self.run_btn.clicked.connect(self.run)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(head)
        ll.addWidget(self.form, 1)
        if module == "transformer":
            ll.addWidget(self.tune)
        ll.addWidget(self.run_btn)

        self.banner = QLabel("Enter inputs and press Run (Ctrl+R)")
        self.banner.setObjectName("banner")
        self.banner.setAlignment(Qt.AlignCenter)
        self.report = QTextBrowser()
        self.report.setOpenExternalLinks(True)
        self.drawing = CrossSection()
        tabs = QTabWidget()
        tabs.addTab(self.report, "Calculation")
        if module in ("cablebus", "bus"):
            tabs.addTab(self.drawing, "Cross-section")
        self.tabs = tabs
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(self.banner)
        rl.addWidget(tabs, 1)

        split = QSplitter()
        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([420, 820])
        lay = QHBoxLayout(self)
        lay.addWidget(split)
        self.last: tuple[Case, object] | None = None

    def case(self, meta: dict) -> Case:
        opts = {"tune_impedance": self.tune.isChecked()} if self.module == "transformer" else {}
        return Case(module=self.module, inputs=self.form.values(), options=opts, **meta)

    def load_case(self, case: Case) -> None:
        self.form.set_values(case.inputs)
        if self.module == "transformer":
            self.tune.setChecked(bool(case.options.get("tune_impedance")))

    def run(self):
        try:
            case = self.case(self.window().meta())
            case.input_object()
        except ValueError as e:
            self._fail(str(e))
            return
        self.run_btn.setEnabled(False)
        self.banner.setText("Calculating…")
        self.banner.setProperty("state", "busy")
        self._restyle()
        job = Job(case)
        job.signals.done.connect(self._done)
        job.signals.failed.connect(self._fail)
        QThreadPool.globalInstance().start(job)

    def _done(self, case: Case, result):
        self.run_btn.setEnabled(True)
        self.last = (case, result)
        passed = bool(getattr(result, "passed", True)) and not (case.module == "feeder" and not result.recommended)
        self.banner.setText(("✔  PASS" if passed else "✖  FAIL") + f"   ·   input hash {case.input_hash()}")
        self.banner.setProperty("state", "pass" if passed else "fail")
        self._restyle()
        html_doc = render(case, result, results_first=True)
        self.report.setHtml(with_figures(self.report.document(), html_doc))
        if case.module == "cablebus":
            self.drawing.show_cablebus(case.input_object(), result)
        elif case.module == "bus":
            self.drawing.show_bus(case.input_object(), result)
        self.status.emit(f"{MODULE_INFO[case.module][0]}: {'PASS' if passed else 'FAIL'}")

    def _fail(self, msg: str):
        self.run_btn.setEnabled(True)
        self.banner.setText("Input or calculation error - see details")
        self.banner.setProperty("state", "fail")
        self._restyle()
        self.report.setPlainText(msg)
        self.drawing.clear()

    def _restyle(self):
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)


# --- cable bus designer page --------------------------------------------------------

OPTION_COLUMNS = ["#", "Result", "Conductors per phase", "Tiers", "Phase pattern", "Enclosure (in)", "Loading %",
                  "VD %", "Losses kW", "Cu mm²/phase", "Block MPa", "Notes"]


class DesignerPage(QWidget):
    status = Signal(str)
    open_in_check = Signal(dict)

    def __init__(self):
        super().__init__()
        title, _, blurb = MODULE_INFO_DESIGN
        self.form = InputForm("designer")
        self.form.set_values({"fault_ka": 65.0, "x_over_r": 20.0})
        head = QLabel(f"<b style='font-size:15pt'>{title}</b><br><span>{blurb}</span>")
        head.setWordWrap(True)
        self.run_btn = QPushButton("Find designs")
        self.run_btn.setObjectName("primary")
        self.run_btn.clicked.connect(self.run)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(head)
        ll.addWidget(self.form, 1)
        ll.addWidget(self.run_btn)

        self.banner = QLabel("Set the requirement and press Find designs")
        self.banner.setObjectName("banner")
        self.banner.setAlignment(Qt.AlignCenter)
        self.table = QTableWidget(0, len(OPTION_COLUMNS))
        self.table.setHorizontalHeaderLabels(OPTION_COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self.show_selected)
        self.svg = QSvgWidget()
        self.svg.setMinimumHeight(260)
        self.detail = QLabel("")
        self.detail.setWordWrap(True)
        self.open_btn = QPushButton("Open selected design in Cable Bus check →")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open)
        fig = QWidget()
        fl = QVBoxLayout(fig)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addWidget(self.svg, 1)
        fl.addWidget(self.detail)
        fl.addWidget(self.open_btn)
        rsplit = QSplitter(Qt.Vertical)
        rsplit.addWidget(self.table)
        rsplit.addWidget(fig)
        rsplit.setSizes([300, 460])
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(self.banner)
        rl.addWidget(rsplit, 1)
        split = QSplitter()
        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([480, 900])
        QHBoxLayout(self).addWidget(split)
        self.result = None

    def run(self):
        try:
            req = DesignRequest(**self.form.values())
        except (ValueError, TypeError) as e:
            self._fail(str(e))
            return
        self.run_btn.setEnabled(False)
        self.banner.setText("Generating and checking designs…")
        self.banner.setProperty("state", "busy")
        self._restyle()
        job = Job(req, design_options)
        job.signals.done.connect(self._done)
        job.signals.failed.connect(self._fail)
        QThreadPool.globalInstance().start(job)

    def _done(self, req, result):
        self.run_btn.setEnabled(True)
        self.result = result
        n_pass = sum(o.passed for o in result.options)
        self.banner.setText(f"{n_pass} passing design(s) shown of {result.considered} checked  ·  "
                            f"{req.voltage_v:g} V, {req.current_a:g} A, {req.code}")
        self.banner.setProperty("state", "pass" if n_pass else "fail")
        self._restyle()
        self.table.setRowCount(0)
        for o in result.options:
            row = self.table.rowCount()
            self.table.insertRow(row)
            cells = [o.rank, "PASS" if o.passed else "FAIL", f"{o.per_phase} x {o.size}", o.tiers, o.pattern,
                     o.enclosure_in, o.max_loading_pct, o.vd_pct, o.loss_kw, o.copper_mm2_per_phase,
                     "" if o.block_stress_mpa is None else f"{o.block_stress_mpa} / {o.block_allowable_mpa}",
                     ", ".join(o.tags) or "; ".join(o.failed_checks)]
            for col, v in enumerate(cells):
                item = QTableWidgetItem(str(v))
                if col == 1:
                    item.setForeground(QColor("#1a7f37" if o.passed else "#c62828"))
                self.table.setItem(row, col, item)
        if result.options:
            self.table.selectRow(0)
        self.status.emit(self.banner.text())

    def show_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows or not self.result:
            return
        o = self.result.options[rows[0].row()]
        inp = CableBusInput(**o.case_inputs)
        r = analyse(inp)
        self.svg.load(QByteArray(cablebus_svg(inp, r, self.result.request.block_material).encode()))
        self.svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
        self.detail.setText(f"<b>{o.label}</b> · pattern {o.pattern} · cable OD {o.cable_od_mm} mm · inside "
                            f"{o.inside_w_mm:.0f} x {o.inside_h_mm:.0f} mm · worst cable {o.max_loading_pct} % · "
                            f"enclosure loss {o.enclosure_loss_kw} kW"
                            + (f" · block {o.block_load_n} N" if o.block_load_n else ""))
        self.open_btn.setEnabled(True)
        self._selected = o

    def _open(self):
        self.open_in_check.emit(dict(self._selected.case_inputs))

    def _fail(self, msg):
        self.run_btn.setEnabled(True)
        self.banner.setText(msg.splitlines()[0][:160])
        self.banner.setProperty("state", "fail")
        self._restyle()

    def _restyle(self):
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)


# --- main window ----------------------------------------------------------------

LIGHT_QSS = """
QListWidget#nav{background:#1f2a37;color:#dbe4ee;border:none;font-size:11pt;padding-top:8px}
QListWidget#nav::item{padding:10px 14px;border-radius:6px;margin:2px 8px}
QListWidget#nav::item:selected{background:#2f6fd6;color:white}
QLabel#banner{padding:10px;border-radius:6px;font-size:12pt;font-weight:600;background:palette(alternate-base)}
QLabel#banner[state="pass"]{background:#e3f4e8;color:#14532d}
QLabel#banner[state="fail"]{background:#fde5e5;color:#7f1d1d}
QLabel#banner[state="busy"]{background:#fff4d6;color:#6b4e00}
QPushButton#primary{background:#2f6fd6;color:white;padding:9px;border-radius:6px;font-weight:600}
QPushButton#primary:disabled{background:#8aa8db}
QGroupBox{font-weight:600;margin-top:10px}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1360, 860)
        self.current_file: Path | None = None
        self.project = QLineEdit()
        self.project.setPlaceholderText("Project")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Calculation title")
        self.revision = QLineEdit("A")
        self.revision.setMaximumWidth(60)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(200)
        self.stack = QStackedWidget()
        self.pages: dict[str, ModulePage] = {}
        self.designer = DesignerPage()
        self.designer.status.connect(lambda s: self.statusBar().showMessage(s, 8000))
        self.designer.open_in_check.connect(self.open_design)
        self.nav.addItem(QListWidgetItem("★ Cable Bus Designer"))
        self.stack.addWidget(self.designer)
        for key, (title, _, _) in MODULE_INFO.items():
            self.nav.addItem(QListWidgetItem(title))
            page = ModulePage(key)
            page.status.connect(lambda s: self.statusBar().showMessage(s, 8000))
            self.pages[key] = page
            self.stack.addWidget(page)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)

        central = QWidget()
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.nav)
        lay.addWidget(self.stack, 1)
        self.setCentralWidget(central)
        self._toolbar()
        self.statusBar().showMessage(f"pecalc engine {__version__} · engineering aid - results need review by a "
                                     "licensed engineer")

    def _toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        def act(text, slot, key=None):
            a = QAction(text, self)
            if key:
                a.setShortcut(QKeySequence(key))
            a.triggered.connect(slot)
            tb.addAction(a)
            return a
        act("New", self.new_case, "Ctrl+N")
        act("Open…", self.open_case, "Ctrl+O")
        act("Save", self.save_case, "Ctrl+S")
        act("Export report…", self.export_report, "Ctrl+E")
        tb.addSeparator()
        self.examples = QComboBox()
        self.examples.addItem("Load example…")
        for f in sorted(EXAMPLES.glob("*.json")):
            self.examples.addItem(f.stem, str(f))
        self.examples.activated.connect(self.load_example)
        tb.addWidget(self.examples)
        tb.addSeparator()
        act("Dark / light", self.toggle_theme)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)
        for w in (QLabel(" Project "), self.project, QLabel("  Title "), self.title_edit, QLabel("  Rev "),
                  self.revision):
            tb.addWidget(w)

    def meta(self) -> dict:
        return {"project": self.project.text(), "title": self.title_edit.text(), "revision": self.revision.text()}

    def show_case(self, case: Case, path: Path | None):
        idx = list(MODULE_INFO).index(case.module) + 1
        self.nav.setCurrentRow(idx)
        self.project.setText(case.project)
        self.title_edit.setText(case.title)
        self.revision.setText(case.revision)
        self.pages[case.module].load_case(case)
        self.current_file = path
        self.setWindowTitle(f"{APP_NAME} - {path.name if path else case.title or case.module}")
        self.pages[case.module].run()

    def open_design(self, inputs: dict):
        inputs = {k: (list(v) if isinstance(v, tuple) else v) for k, v in inputs.items()}
        self.show_case(Case(module="cablebus", inputs=inputs, project=self.project.text(),
                            title=self.title_edit.text() or "Cable bus design", revision=self.revision.text()), None)

    def page(self):
        w = self.stack.currentWidget()
        return w if isinstance(w, ModulePage) else self.pages["cablebus"]

    def new_case(self):
        self.page().form.set_values({})
        self.current_file = None
        self.setWindowTitle(APP_NAME)

    def open_case(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Open case", str(EXAMPLES), "Case files (*.json)")
        if fn:
            try:
                self.show_case(Case.load(fn), Path(fn))
            except (ValueError, OSError, json.JSONDecodeError) as e:
                QMessageBox.warning(self, "Cannot open case", str(e))

    def load_example(self, i: int):
        if i > 0:
            self.show_case(Case.load(self.examples.itemData(i)), None)
            self.examples.setCurrentIndex(0)

    def save_case(self):
        try:
            case = self.page().case(self.meta())
        except ValueError as e:
            QMessageBox.warning(self, "Cannot save", str(e))
            return
        fn = str(self.current_file) if self.current_file else QFileDialog.getSaveFileName(
            self, "Save case", f"{case.title or case.module}.json", "Case files (*.json)")[0]
        if fn:
            inputs = {k: v for k, v in case.inputs.items()}
            Case(case.module, inputs, case.project, case.title, case.revision, case.options).save(fn)
            self.current_file = Path(fn)
            self.statusBar().showMessage(f"Saved {fn}", 6000)

    def export_report(self):
        last = self.page().last
        if not last:
            QMessageBox.information(self, "Nothing to export", "Run the calculation first.")
            return
        case, result = last
        fn, chosen = QFileDialog.getSaveFileName(self, "Export calculation report", f"{case.title or case.module}.pdf",
                                                 "PDF document (*.pdf);;HTML report (*.html)")
        if not fn:
            return
        if fn.lower().endswith(".html") or chosen.startswith("HTML"):
            fn = fn if fn.lower().endswith(".html") else fn + ".html"
            Path(fn).write_text(render(case, result), encoding="utf-8")
        else:
            fn = fn if fn.lower().endswith(".pdf") else fn + ".pdf"
            export_pdf(render(case, result), fn)
        self.statusBar().showMessage(f"Report written to {fn}", 8000)

    def toggle_theme(self):
        app = QApplication.instance()
        dark = app.property("dark") is not True
        apply_theme(app, dark)


def export_pdf(html_doc: str, path: str) -> None:
    """Write a calculation package to PDF (Letter, 15 mm margins)."""
    writer = QPdfWriter(path)
    writer.setResolution(96)
    writer.setPageLayout(QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Portrait,
                                     QMarginsF(15, 15, 15, 15), QPageLayout.Millimeter))
    writer.setTitle("Calculation package")
    writer.setCreator(APP_NAME)
    doc = QTextDocument()
    doc.setDefaultFont(QFont("Helvetica", 9))
    doc.setHtml(with_figures(doc, html_doc, 680))
    doc.setPageSize(writer.pageLayout().paintRectPixels(writer.resolution()).size().toSizeF())
    doc.print_(writer)


def apply_theme(app: QApplication, dark: bool) -> None:
    app.setProperty("dark", dark)
    app.setStyle(QStyleFactory.create("Fusion"))
    pal = QPalette()
    if dark:
        for role, c in ((QPalette.Window, "#1b1f24"), (QPalette.WindowText, "#e6e6e6"), (QPalette.Base, "#14171b"),
                        (QPalette.AlternateBase, "#22272e"), (QPalette.Text, "#e6e6e6"), (QPalette.Button, "#262c33"),
                        (QPalette.ButtonText, "#e6e6e6"), (QPalette.Highlight, "#2f6fd6"),
                        (QPalette.HighlightedText, "#ffffff"), (QPalette.ToolTipBase, "#22272e"),
                        (QPalette.ToolTipText, "#e6e6e6"), (QPalette.PlaceholderText, "#8b949e"),
                        (QPalette.Mid, "#6b7785")):
            pal.setColor(role, QColor(c))
    else:
        for role, c in ((QPalette.Window, "#f4f6f8"), (QPalette.WindowText, "#1a1f24"), (QPalette.Base, "#ffffff"),
                        (QPalette.AlternateBase, "#eef1f4"), (QPalette.Text, "#1a1f24"), (QPalette.Button, "#ffffff"),
                        (QPalette.ButtonText, "#1a1f24"), (QPalette.Highlight, "#2f6fd6"),
                        (QPalette.HighlightedText, "#ffffff"), (QPalette.ToolTipBase, "#ffffff"),
                        (QPalette.ToolTipText, "#1a1f24"), (QPalette.PlaceholderText, "#8a96a3"),
                        (QPalette.Mid, "#6b7785")):
            pal.setColor(role, QColor(c))
    app.setPalette(pal)
    app.setStyleSheet(LIGHT_QSS)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setDesktopFileName("power-equipment-studio")
    app.setWindowIcon(QIcon(str(ICON)))
    apply_theme(app, dark=False)
    win = MainWindow()
    win.show()
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        win.show_case(Case.load(sys.argv[1]), Path(sys.argv[1]))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
