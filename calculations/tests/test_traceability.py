"""Traceability: table data fingerprint, engine stamp on case files, report header."""

import io
import json
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from pecalc import __version__, datainfo
from pecalc.__main__ import main
from pecalc.cases import Case
from pecalc.report import render

FEEDER = {"module": "feeder", "title": "Trace test", "inputs": {"continuous_a": 100, "length_m": 30}}


class Fingerprint(unittest.TestCase):
    def test_format_and_stable(self):
        fp = datainfo.data_fingerprint()
        self.assertRegex(fp, r"^[0-9a-f]{12}$")
        datainfo.data_fingerprint.cache_clear()
        self.assertEqual(datainfo.data_fingerprint(), fp)

    def test_ignores_line_endings_and_key_order(self):
        # Same content with CRLF and reversed keys gives the same canonical text.
        with tempfile.TemporaryDirectory() as d:
            src = datainfo.DATA_DIR / "nec_240_4d_small_conductors.json"
            a, b = Path(d, "a.json"), Path(d, "b.json")
            shutil.copy(src, a)
            obj = json.loads(src.read_text(encoding="utf-8"))
            b.write_bytes(json.dumps(dict(reversed(list(obj.items()))), indent=3).replace("\n", "\r\n").encode())
            self.assertEqual(datainfo._canonical(a), datainfo._canonical(b))

    def test_changes_with_data(self):
        with tempfile.TemporaryDirectory() as d:
            for p in datainfo.DATA_DIR.glob("*.json"):
                shutil.copy(p, d)
            f = Path(d, "nec_240_4d_small_conductors.json")
            obj = json.loads(f.read_text(encoding="utf-8"))
            obj["Cu"]["14"] = 16
            f.write_text(json.dumps(obj), encoding="utf-8")
            old_dir, old = datainfo.DATA_DIR, datainfo.data_fingerprint()
            try:
                datainfo.DATA_DIR = Path(d)
                datainfo.data_fingerprint.cache_clear()
                self.assertNotEqual(datainfo.data_fingerprint(), old)
            finally:
                datainfo.DATA_DIR = old_dir
                datainfo.data_fingerprint.cache_clear()

    def test_data_tables_lists_status(self):
        rows = {r["file"]: r for r in datainfo.data_tables()}
        self.assertEqual(rows["ampacity_nec.json"]["status"], "UNVERIFIED")
        self.assertEqual(rows["ampacity_cec.json"]["status"], "PLACEHOLDER")


class CaseStamp(unittest.TestCase):
    def test_save_writes_stamp_and_load_reads_it(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "c.json")
            Case(**FEEDER).save(p)
            saved = json.loads(p.read_text())
            self.assertEqual(saved["engine"], {"pecalc": __version__, "data": datainfo.data_fingerprint()})
            c = Case.load(p)
            self.assertEqual(c.engine_mismatch(), "")

    def test_old_file_without_stamp_loads(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "old.json")
            p.write_text(json.dumps(FEEDER))
            self.assertEqual(Case.load(p).engine_mismatch(), "")

    def test_mismatch_is_reported(self):
        c = Case(**FEEDER, engine={"pecalc": "0.0.1", "data": "000000000000"})
        msg = c.engine_mismatch()
        self.assertIn("pecalc 0.0.1", msg)
        self.assertIn("data 000000000000", msg)
        html_doc = render(c, c.run())
        self.assertIn("Case file saved with", html_doc)


class ReportAndCli(unittest.TestCase):
    def test_report_header_has_fingerprint(self):
        c = Case(**FEEDER)
        self.assertIn(datainfo.data_fingerprint(), render(c, c.run()))

    def test_version_flag(self):
        buf = io.StringIO()
        with redirect_stdout(buf), self.assertRaises(SystemExit) as e:
            main(["--version"])
        self.assertEqual(e.exception.code, 0)
        self.assertTrue(re.match(rf"pecalc {re.escape(__version__)}, table data [0-9a-f]{{12}}", buf.getvalue()))


if __name__ == "__main__":
    unittest.main()
