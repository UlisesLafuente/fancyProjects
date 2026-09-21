# -*- mode: python ; coding: utf-8 -*-
import re
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
VERSION = re.search(r'__version__ = "([^"]+)"', (ROOT / "src" / "__init__.py").read_text()).group(1)

a = Analysis(
    [str(ROOT / "packaging" / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[
        (str(ROOT / "src" / "appWindow" / "style.css"), "."),
        (str(ROOT / "src" / "res"), "res"),
    ],
    hiddenimports=["gi", "appWindow", "appWindow.hour_grid", "persistence", "projects"],
    hookspath=[],
    hooksconfig={
        "gi": {
            "icons": ["Adwaita", "hicolor"],
            "themes": ["Adwaita"],
            "languages": [],
            "module-versions": {
                "Gtk": "4.0",
                "Gdk": "4.0",
                "Adw": "1",
                "GdkPixbuf": "2.0",
            },
        },
    },
    runtime_hooks=[str(ROOT / "packaging" / "runtime_hook.py")],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide6", "PySide2", "matplotlib", "numpy"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="fanzyprojects",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="fanzyprojects",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Fanzy Projects.app",
        bundle_identifier="com.ulises.fanzyprojects",
        icon=str(ROOT / "packaging" / "icon.icns"),
        version=VERSION,
    )