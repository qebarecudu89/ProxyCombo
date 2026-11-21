import os
import shutil
import subprocess
import sys
from .config import BASE_DIR

def build_exe() -> bool:
    script = os.path.join(BASE_DIR, "main.py")
    for pkg in ("flet[all]", "psutil", "requests[socks]", "pysocks",
                "pyinstaller", "certifi"):
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", pkg],
                       capture_output=True, creationflags=0x08000000)
    for folder in ("build", "dist"):
        p = os.path.join(BASE_DIR, folder)
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "ProxyCombo",
        "--collect-all", "flet", "--collect-all", "flet_desktop",
        "--hidden-import", "flet", "--hidden-import", "flet_desktop",
        "--hidden-import", "psutil", "--hidden-import", "requests",
        "--hidden-import", "socks",
        script,
    ]
    r = subprocess.run(cmd, cwd=BASE_DIR)
    return r.returncode == 0 and os.path.exists(
        os.path.join(BASE_DIR, "dist", "ProxyCombo.exe"))