"""Build a standalone Power Equipment Studio app with PyInstaller (Windows, Linux or macOS).

    pip install -r app/requirements.txt pyinstaller
    python app/build.py            ->  dist/PowerEquipmentStudio/ (folder with the executable)
"""
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "PowerEquipmentStudio"


def main() -> int:
    icon = ROOT / "app" / "assets" / "icon.png"
    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--name", NAME,
        "--paths", str(ROOT / "calculations"),
        "--add-data", f"{ROOT / 'calculations' / 'pecalc' / 'data'}:pecalc/data",
        "--add-data", f"{ROOT / 'examples'}:examples",
        "--add-data", f"{icon}:app/assets",
        "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"), "--specpath", str(ROOT / "build"),
        # Only the Qt pieces the app uses; keeps the bundle small.
        "--exclude-module", "tkinter",
    ]
    if platform.system() in ("Windows", "Darwin"):
        args += ["--icon", str(icon)]  # PyInstaller converts PNG with Pillow
    args.append(str(ROOT / "app" / "main.py"))
    subprocess.run(args, check=True)
    out = ROOT / "dist" / NAME
    shutil.copy(ROOT / "LICENSE", out / "LICENSE.txt")
    print(f"Built {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
