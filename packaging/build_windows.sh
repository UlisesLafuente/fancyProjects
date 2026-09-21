#!/bin/bash
# Ejecutar dentro del shell UCRT64 de MSYS2 en un runner de Windows.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
SRC="$(cygpath -m "$ROOT/src")"

VERSION="$(python -c "import sys; sys.path.insert(0, '$SRC'); import src; print(src.__version__)")"
echo "Versión: $VERSION"

echo "==> Dependencias MSYS2 (ucrt64)"
pacman -Sy --needed --noconfirm \
    mingw-w64-ucrt-x86_64-python \
    mingw-w64-ucrt-x86_64-python-pip \
    mingw-w64-ucrt-x86_64-python-gobject \
    mingw-w64-ucrt-x86_64-gtk4 \
    mingw-w64-ucrt-x86_64-libadwaita \
    mingw-w64-ucrt-x86_64-nsis

echo "==> PyInstaller"
python -m pip install --quiet --upgrade pyinstaller

rm -rf build/pyi_win dist/fancyprojects
SPEC="$(cygpath -m "$ROOT/packaging/fancyprojects.spec")"
python -m PyInstaller --noconfirm --clean "$SPEC"

echo "==> Instalador NSIS"
sed "s/{{VERSION}}/${VERSION}/" packaging/fancyprojects.nsi > build/fancyprojects.nsi
makensis build/fancyprojects.nsi
ls -lh "dist/FancyProjects-${VERSION}-windows-installer.exe"

echo "==> Smoke test"
BIN="dist/fancyprojects/fancyprojects.exe"
LOG="/tmp/fancyprojects-windows-smoke.log"
rm -f "$LOG"
"$BIN" >"$LOG" 2>&1 &
PID=$!
sleep 6
if kill -0 "$PID" 2>/dev/null; then
    echo "App viva a los 6s -> OK"
    taskkill //IM fancyprojects.exe //F >/dev/null 2>&1 || kill "$PID"
elif wait "$PID"; then
    echo "App terminó limpiamente -> OK"
else
    echo "App terminó con error -> FALLO"
    echo "---- salida de la app ----"
    sed -n '1,40p' "$LOG"
    echo "--------------------------"
    exit 1
fi