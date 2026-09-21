#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION="$(".venv/bin/python" -c "import sys; sys.path.insert(0, '$ROOT/src'); import src; print(src.__version__)")"
ARCH="${ARCH:-x86_64}"
APPIMAGE_TOOL="${APPIMAGE_TOOL:-build/appimagetool-x86_64.AppImage}"

if [ ! -x ".venv/bin/python" ]; then
    echo "No hay .venv; creándolo con paquetes de sistema..."
    python3 -m venv --system-site-packages .venv
fi
.venv/bin/python -m pip install --quiet --upgrade pyinstaller

echo "==> PyInstaller (spec $PWD/packaging/fancyprojects.spec)"
.venv/bin/pyinstaller --noconfirm --distpath "$ROOT/dist/appimage_dist" "$ROOT/packaging/fancyprojects.spec"

echo "==> Ensamblando AppDir"
APPDIR="build/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/scalable/apps" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp -r dist/appimage_dist/fancyprojects/. "$APPDIR/usr/bin/"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
exec "$APPDIR/usr/bin/fancyprojects" "$@"
EOF
chmod +x "$APPDIR/AppRun"

cp packaging/com.ulises.fancyprojects.desktop "$APPDIR/usr/share/applications/"
cp packaging/com.ulises.fancyprojects.metainfo.xml "$APPDIR/usr/share/metainfo/" 2>/dev/null || { mkdir -p "$APPDIR/usr/share/metainfo"; cp packaging/com.ulises.fancyprojects.metainfo.xml "$APPDIR/usr/share/metainfo/"; }
cp packaging/icons/hicolor/scalable/apps/com.ulises.fancyprojects.svg "$APPDIR/usr/share/icons/hicolor/scalable/apps/"
cp packaging/icons/hicolor/256x256/apps/com.ulises.fancyprojects.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/"
cp packaging/icons/hicolor/256x256/apps/com.ulises.fancyprojects.png "$APPDIR/com.ulises.fancyprojects.png"
cp packaging/com.ulises.fancyprojects.desktop "$APPDIR/com.ulises.fancyprojects.desktop"

# Icono raíz para appimagetool
cp packaging/icons/hicolor/scalable/apps/com.ulises.fancyprojects.svg "$APPDIR/com.ulises.fancyprojects.svg"

if [ ! -x "$APPIMAGE_TOOL" ]; then
    echo "==> Descargando appimagetool"
    mkdir -p build
    curl -sSL -o "$APPIMAGE_TOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
    chmod +x "$APPIMAGE_TOOL"
fi

echo "==> Generando AppImage"
rm -f "dist/FancyProjects-${VERSION}-${ARCH}.AppImage"
APPIMAGE_EXTRACT_AND_RUN=1 ARCH="$ARCH" "$APPIMAGE_TOOL" "$APPDIR" "dist/FancyProjects-${VERSION}-${ARCH}.AppImage"
ls -lh "dist/FancyProjects-${VERSION}-${ARCH}.AppImage"