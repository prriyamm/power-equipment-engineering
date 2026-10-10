#!/usr/bin/env sh
# Install a built Power Equipment Studio into ~/.local and add it to the application launcher.
# Usage: app/install_linux.sh [path-to-built-folder]   (default: dist/PowerEquipmentStudio)
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
src=${1:-$here/dist/PowerEquipmentStudio}
[ -x "$src/PowerEquipmentStudio" ] || { echo "Build not found at $src (run: python app/build.py)"; exit 1; }
dest="$HOME/.local/opt/power-equipment-studio"
rm -rf "$dest" && mkdir -p "$dest" "$HOME/.local/bin" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/512x512/apps"
cp -r "$src"/. "$dest"/
ln -sf "$dest/PowerEquipmentStudio" "$HOME/.local/bin/power-equipment-studio"
cp "$here/app/assets/icon.png" "$HOME/.local/share/icons/hicolor/512x512/apps/power-equipment-studio.png"
cat > "$HOME/.local/share/applications/power-equipment-studio.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Power Equipment Studio
Comment=Engineering calculations for switchgear, transformers and cable bus
Exec=$dest/PowerEquipmentStudio %f
Icon=power-equipment-studio
Terminal=false
Categories=Engineering;Science;Utility;
MimeType=application/json;
StartupWMClass=power-equipment-studio
DESKTOP
command -v update-desktop-database >/dev/null && update-desktop-database "$HOME/.local/share/applications" || true
echo "Installed to $dest - launch 'Power Equipment Studio' from your app launcher or run power-equipment-studio"
