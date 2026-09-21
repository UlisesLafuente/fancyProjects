#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -x "$ROOT/.venv/bin/python" ]; then
    PY="$ROOT/.venv/bin/python"
else
    PY="${PYTHON:-python3}"
fi
VERSION="$("$PY" -c "import sys; sys.path.insert(0, '$ROOT/src'); import src; print(src.__version__)")"

STAGE="$ROOT/dist/deb"
OUT="$ROOT/dist/fancyprojects_${VERSION}_all.deb"

rm -rf "$STAGE"
mkdir -p "$STAGE/DEBIAN" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/share/fancyprojects" \
         "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/metainfo"

cp "$ROOT/packaging/deb/DEBIAN/control" "$STAGE/DEBIAN/control"
sed -i "s/^Version: .*/Version: ${VERSION}/" "$STAGE/DEBIAN/control"

cp -r "$ROOT/src" "$STAGE/usr/share/fancyprojects/src"
cp "$ROOT/packaging/deb/usr/share/fancyprojects/fancyprojects.py" "$STAGE/usr/share/fancyprojects/"

install -m 755 "$ROOT/packaging/deb/usr/bin/fancyprojects" "$STAGE/usr/bin/"

for size in 16 32 48 64 128 256 512; do
    mkdir -p "$STAGE/usr/share/icons/hicolor/${size}x${size}/apps"
    cp "$ROOT/packaging/icons/hicolor/${size}x${size}/apps/com.ulises.fancyprojects.png" \
       "$STAGE/usr/share/icons/hicolor/${size}x${size}/apps/"
done
mkdir -p "$STAGE/usr/share/icons/hicolor/scalable/apps"
cp "$ROOT/packaging/icons/hicolor/scalable/apps/com.ulises.fancyprojects.svg" \
   "$STAGE/usr/share/icons/hicolor/scalable/apps/"

cp "$ROOT/packaging/com.ulises.fancyprojects.desktop" "$STAGE/usr/share/applications/"
cp "$ROOT/packaging/com.ulises.fancyprojects.metainfo.xml" "$STAGE/usr/share/metainfo/"

dpkg-deb --build --root-owner-group "$STAGE" "$OUT"
echo "Creado: $OUT"
dpkg-deb --info "$OUT" | sed -n '1,25p'