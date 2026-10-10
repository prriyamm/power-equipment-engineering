# Power Equipment Studio (desktop app)

A native desktop application (Qt / PySide6) for the `pecalc` engine: feeder & cable sizing, cable bus, switchgear bus, transformer and lug modules, with case files, a cross-section view and calculation reports exported as PDF or HTML.

## Install

Download the latest build from the repository's **Releases** page:

- **Windows:** `PowerEquipmentStudio-<version>-windows-setup.exe` (installer with Start-menu and optional desktop shortcut), or the portable zip. Builds are not code-signed yet, so Windows SmartScreen may ask you to confirm ("More info" → "Run anyway").
- **Linux:** extract `PowerEquipmentStudio-<version>-linux-x86_64.tar.gz`, then run `PowerEquipmentStudio/install_linux.sh PowerEquipmentStudio` to add it to your application launcher.
- **macOS:** unzip and open `PowerEquipmentStudio.app` (unsigned: right-click → Open the first time).

## Run from source

```
python -m venv .venv
.venv/bin/pip install -r app/requirements.txt      # Windows: .venv\Scripts\pip
.venv/bin/python app/main.py [case.json]
```

## Build

```
.venv/bin/pip install pyinstaller pillow
.venv/bin/python app/build.py                      # -> dist/PowerEquipmentStudio/
dist/PowerEquipmentStudio/PowerEquipmentStudio --selftest
app/install_linux.sh                               # Linux: install into ~/.local and the launcher
```

Release builds for Windows, Linux and macOS are produced by `.github/workflows/release.yml` when a `v*` tag is pushed.
