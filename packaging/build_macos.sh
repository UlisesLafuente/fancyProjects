#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION="$("$ROOT/.venv/bin/python" -c "import sys; sys.path.insert(0, '$ROOT/src'); import src; print(src.__version__)")"
echo "Versión: $VERSION"

echo "==> Dependencias (Homebrew)"
for pkg in gtk4 libadwaita pygobject3 adwaita-icon-theme; do
    brew list "$pkg" >/dev/null 2>&1 || brew install "$pkg"
done

echo "==> Entorno virtual"
if [ ! -x ".venv/bin/python" ]; then
    python3 -m venv --system-site-packages .venv
fi
.venv/bin/python -m pip install --quiet --upgrade pyinstaller

echo "==> Icono .icns"
ICONSET="build/icon.iconset"
rm -rf "$ICONSET"
mkdir -p "$ICONSET"
SRC="packaging/icons/hicolor/512x512/apps/com.ulises.fancyprojects.png"
for size in 16 32 128 256 512; do
    sips -z "$size" "$size" "$SRC" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
done
sips -z 32 32 "$SRC" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
sips -z 64 64 "$SRC" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
sips -z 256 256 "$SRC" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z 512 512 "$SRC" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z 1024 1024 "$SRC" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
iconutil -c icns "$ICONSET" -o packaging/icon.icns

echo "==> PyInstaller"
rm -rf build/pyi_mac dist/Fancy\ Projects.app
.venv/bin/pyinstaller --noconfirm --clean \
    --distpath "$ROOT/dist" \
    --workpath "$ROOT/build/pyi_mac" \
    --specpath "$ROOT/build" \
    "$ROOT/packaging/fancyprojects.spec"

echo "==> Firma ad-hoc"
codesign --force --deep --sign - "dist/Fancy Projects.app"
codesign --verify --deep "dist/Fancy Projects.app"

echo "==> Firma binario interno (por si Gatekeeper lo pide)"
codesign --force --sign - "dist/Fancy Projects.app/Contents/MacOS/fancyprojects"

echo "==> DMG"
rm -f "dist/FancyProjects-${VERSION}-macos.dmg"
hdiutil create -volname "Fancy Projects" -srcfolder "dist/Fancy Projects.app" \
    -ov -format UDZO "dist/FancyProjects-${VERSION}-macos.dmg"
ls -lh "dist/FancyProjects-${VERSION}-macos.dmg"

echo "==> Smoke test"
BIN="dist/Fancy Projects.app/Contents/MacOS/fancyprojects"
"$BIN" &
PID=$!
sleep 6
if kill -0 "$PID" 2>/dev/null; then
    echo "App viva a los 6s -> OK"
    kill "$PID"
    wait "$PID" 2>/dev/null || true
else
    wait "$PID"
    echo "App terminó antes de tiempo (exit=$?) -> FALLO"
    exit 1
fi