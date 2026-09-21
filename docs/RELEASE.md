# Releases

La app es Python + PyGObject + GTK4 + libadwaita. Se publica en 4 formatos.

## Artefactos

| Formato | Script | Base de build | Notas |
|---|---|---|---|
| `.deb` | `packaging/build_deb.sh` | Ubuntu 24.04 | Depende de paquetes de sistema (`python3-gi`, `gir1.2-gtk-4.0`, `libadwaita-1-0`, `gir1.2-adw-1`) |
| AppImage | `packaging/build_appimage.sh` | Ubuntu 24.04 | Empaqueta su propio GTK/libadwaita. **Suelo glibc 2.39** (Ubuntu 24.04+, Debian 13+, Mint 22+) |
| `.dmg` | `packaging/build_macos.sh` | `macos-latest` (arm64) | Sin firmar/notarizar → Gatekeeper pide "Abrir" con clic derecho |
| instaler `.exe` | `packaging/build_windows.sh` | MSYS2 UCRT64 + NSIS | GTK4/libadwaita vía MSYS2; el aspecto no es nativo de Windows |

## Decisiones técnicas

- **Windows**: no hay wheels pip oficiales de PyGObject/GTK4. El camino es MSYS2
  (UCRT64) con `mingw-w64-ucrt-x86_64-python-gobject` + `gtk4` + `libadwaita`,
  pico aplicado con PyInstaller. El runtime hook `packaging/runtime_hook.py`
  fija `PYGI_DLL_PATH` a `_internal` en tiempo de ejecución.
- **macOS**: Homebrew provee `pygobject3`, `gtk4` y `libadwaita`. Se firma con
  firma ad-hoc (no notarización) y se empaqueta en `.dmg`.
- **AppImage**: se usa `PyInstaller` (onedir) en un contenedor Ubuntu 24.04 para
  máxima portabilidad razonable. El código usa `Adw.Dialog` (libadwaita >= 1.4),
  por eso no se puede construir sobre 22.04.
- **Estilo**: `src/appWindow/style.css` se embebe en el bundle y se resuelve con
  `appWindow.app_window.resource_path()` (usa `sys._MEIPASS` al estar congelado).

## CI (`release.yml`)

- En cada push a `main` se ejecutan tests + builds y se suben artefactos.
- En un tag `v*` se publica un GitHub Release con los 4 artefactos.
- Cada job hace un smoke test del binario congelado (proceso vivo unos segundos).

## Build local

```sh
# Artefactos de Linux (requieren GI/GTK/libadwaita del sistema)
packaging/build_deb.sh
packaging/build_appimage.sh
```

macOS y Windows solo pueden construirse en sus propios OS (PyInstaller no compila
en cruz); el flujo recomendado es dejar que CI los genere.

## Notas de instalación

- **Windows**: SmartScreen puede avisar al no haber firma de código comercial.
- **macOS**: al no estar notarizado, abrir con clic derecho → "Abrir" la primera vez.
- **Datos**: la base de datos se guarda en `~/.local/share/fanzyProjects/projects.db`
  (se puede sobrescribir con la env var `FANZY_PROJECTS_DB`).