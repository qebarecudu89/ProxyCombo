import subprocess
import sys
import time
from .config import IS_FROZEN, FIRST_RUN_FLAG
from .logging_utils import dbg

def check_windows():
    if sys.platform != "win32":
        print("❌ Только для Windows!")
        sys.exit(1)

def check_python():
    v = sys.version_info
    if v.major == 3 and v.minor >= 15:
        print("=" * 70)
        print("❌ Flet не поддерживает Python 3.15.")
        print(f"   У тебя: Python {v.major}.{v.minor}")
        print("   Требуется: Python 3.10 – 3.14.")
        print("💡 Установи 3.12/3.13: py -3.12 main.py")
        print("=" * 70)
        input("Enter...")
        sys.exit(1)

def _pip(pkg):
    dbg(f"pip install {pkg}")
    print(f"📦 Устанавливаю {pkg}...")
    return subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", pkg],
        capture_output=True, text=True, creationflags=0x08000000,
    ).returncode == 0

def check_dependencies():
    if IS_FROZEN:
        return
    pairs = [
        ("flet", "flet[all]"),
        ("flet_desktop", "flet[all]"),
        ("psutil", "psutil"),
        ("requests", "requests[socks]"),
        ("socks", "pysocks"),
        ("certifi", "certifi"),
    ]
    missing, seen = [], set()
    for mod, pip_name in pairs:
        try:
            __import__(mod)
        except ImportError:
            if pip_name not in seen:
                missing.append(pip_name)
                seen.add(pip_name)
    if not missing:
        return
    print("=" * 60)
    print("🔧 ПЕРВЫЙ ЗАПУСК: устанавливаю зависимости...")
    print("=" * 60)
    for pkg in ["flet[all]", "psutil", "requests[socks]", "pysocks", "certifi"]:
        _pip(pkg)
    try:
        with open(FIRST_RUN_FLAG, "w") as f:
            f.write(f"installed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    except Exception:
        pass
    still = []
    for mod, pip_name in pairs:
        try:
            __import__(mod)
        except ImportError:
            still.append(pip_name)
    if still:
        print(f"❌ Не удалось установить: {still}")
        input("Enter...")
        sys.exit(1)
    print("✅ Зависимости готовы")