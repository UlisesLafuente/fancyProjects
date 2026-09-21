#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Dependencias (Homebrew)"
for pkg in gtk4 libadwaita pygobject3 adwaita-icon-theme python; do
    brew list "$pkg" >/dev/null 2>&1 || brew install "$pkg"
done

echo "==> Entorno virtual (usando el python de Homebrew)"
if [ ! -x ".venv/bin/python" ]; then
    if [ -x "$(brew --prefix)/bin/python3" ]; then
        PYTHON_BIN="$(brew --prefix)/bin/python3"
    else
        PYTHON_BIN="python3"
    fi
    "$PYTHON_BIN" -m venv --system-site-packages .venv
fi
.venv/bin/python -m pip install --quiet --upgrade pyinstaller

VERSION="$(".venv/bin/python" -c "import sys; sys.path.insert(0, '$ROOT/src'); import src; print(src.__version__)")"
echo "Versión: $VERSION"

echo "==> Icono .icns"
ICONSET="build/icon.iconset"
rm -rf "$ICONSET"
mkdir -p "$ICONSET"
SRC="packaging/icons/hicolor/512x512/apps/com.ulises.fanzyprojects.png"
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
    "$ROOT/packaging/fanzyprojects.spec"

echo "==> Firma ad-hoc"
codesign --force --deep --sign - "dist/Fanzy Projects.app"
codesign --verify --deep "dist/Fanzy Projects.app"

echo "==> Firma binario interno (por si Gatekeeper lo pide)"
codesign --force --sign - "dist/Fanzy Projects.app/Contents/MacOS/fanzyprojects"

echo "==> DMG"
rm -f "dist/FanzyProjects-${VERSION}-macos.dmg"
hdiutil create -volname "Fanzy Projects" -srcfolder "dist/Fanzy Projects.app" \
    -ov -format UDZO "dist/FanzyProjects-${VERSION}-macos.dmg"
ls -lh "dist/FanzyProjects-${VERSION}-macos.dmg"

echo "==> Smoke test"
BIN="dist/Fanzy Projects.app/Contents/MacOS/fanzyprojects"
LOG="/tmp/fanzyprojects-macos-smoke.log"
rm -f "$LOG"
"$BIN" >"$LOG" 2>&1 &
PID=$!
sleep 6
if kill -0 "$PID" 2>/dev/null; then
    echo "App viva a los 6s -> OK"
    kill "$PID"
    wait "$PID" 2>/dev/null || true
else
    wait "$PID"
    CODE=$?
    echo "App terminó antes de tiempo (exit=$CODE) -> FALLO"
    echo "---- salida de la app ----"
    sed -n '1,40p' "$LOG"
    echo "--------------------------"
    exit 1
fi