import os
import sys

if sys.platform == "win32":
    internal = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "_internal")
    if os.path.isdir(internal):
        existing = os.environ.get("PYGI_DLL_PATH", "")
        os.environ["PYGI_DLL_PATH"] = internal if not existing else existing + ";" + internal