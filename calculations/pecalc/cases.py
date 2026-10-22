"""Design case files: a saved, versionable set of inputs for one module.

A case file is JSON:

    {
      "project": "Plant expansion",
      "title": "Main switchboard feeder",
      "revision": "A",
      "module": "feeder" | "cablebus" | "bus" | "transformer" | "lugs",
      "options": {"tune_impedance": true},          # module-specific, optional
      "inputs": { ...fields of the module's input dataclass... },
      "engine": {"pecalc": "0.1.0", "data": "<fingerprint>"}   # written by save(), optional
    }

Unknown input names are rejected so a typo cannot silently fall back to a
default. The input hash in reports ties a calculation to its exact inputs; the
engine stamp records the engine version and table data that saved the file.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, fields
from pathlib import Path

from .cablebus import CableBusInput, analyse
from .datainfo import engine_stamp
from .lugs import LugInput, select_lugs
from .sizing import FeederInput, size_feeder
from .switchgear import BusInput, analyse_bus
from .transformer import TransformerInput, design, design_for_impedance

MODULES = {
    "feeder": (FeederInput, lambda i, o: size_feeder(i)),
    "cablebus": (CableBusInput, lambda i, o: analyse(i)),
    "bus": (BusInput, lambda i, o: analyse_bus(i)),
    "transformer": (TransformerInput,
                    lambda i, o: design_for_impedance(i) if o.get("tune_impedance") else design(i)),
    "lugs": (LugInput, lambda i, o: select_lugs(i)),
}


@dataclass
class Case:
    module: str
    inputs: dict
    project: str = ""
    title: str = ""
    revision: str = ""
    options: dict = dataclasses.field(default_factory=dict)
    engine: dict = dataclasses.field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "Case":
        data = json.loads(Path(path).read_text())
        missing = {"module", "inputs"} - data.keys()
        if missing:
            raise ValueError(f"Case file is missing {sorted(missing)}")
        extra = data.keys() - {f.name for f in fields(cls)}
        if extra:
            raise ValueError(f"Unknown case keys {sorted(extra)}")
        return cls(**data)

    def save(self, path: str | Path) -> None:
        self.engine = engine_stamp()
        Path(path).write_text(json.dumps(dataclasses.asdict(self), indent=2) + "\n")

    def engine_mismatch(self) -> str:
        """Empty when the file has no stamp, or was saved by this engine version and table data."""
        now = engine_stamp()
        diff = [f"{k} {self.engine[k]} (now {now[k]})" for k in ("pecalc", "data")
                if self.engine.get(k) and self.engine[k] != now[k]]
        return ("Case file saved with " + ", ".join(diff) + ". Results can differ from the saved run.") if diff else ""

    def input_object(self):
        if self.module not in MODULES:
            raise ValueError(f"module must be one of {sorted(MODULES)}")
        cls = MODULES[self.module][0]
        names = {f.name for f in fields(cls)}
        unknown = set(self.inputs) - names
        if unknown:
            raise ValueError(f"Unknown {self.module} inputs: {sorted(unknown)}")
        kwargs = dict(self.inputs)
        for k, v in kwargs.items():  # JSON lists -> tuples where the dataclass default is a tuple
            default = next(f.default for f in fields(cls) if f.name == k)
            if isinstance(default, tuple) and isinstance(v, list):
                kwargs[k] = tuple(v)
        return cls(**kwargs)

    def input_hash(self) -> str:
        blob = json.dumps({"module": self.module, "inputs": self.inputs, "options": self.options}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]

    def run(self):
        return MODULES[self.module][1](self.input_object(), self.options)
