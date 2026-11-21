import os
import sys

import ssl
ssl._create_default_https_context = ssl._create_unverified_context
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except ImportError:
    pass

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from version import VERSION
from proxycombo.bootstrap import check_python, check_dependencies, check_windows
from proxycombo import app

DEBUG = "--debug" in sys.argv

def main_entry():
    check_windows()
    check_python()
    check_dependencies()

    import flet as ft
    if DEBUG:
        print("=" * 60)
        print(f"🐍 Python {sys.version.split()[0]}")
        print(f"📦 Flet {getattr(ft, '__version__', '?')}")
        print(f"🏷  ProxyCombo {VERSION}")
        print("=" * 60)

    try:
        ft.run(app.main, view=ft.AppView.FLET_APP)
    except Exception as e:
        from proxycombo.logging_utils import fatal
        fatal(e)
        print(f"💥 {e}")
        input("Enter для выхода...")
    finally:
        from proxycombo.system_proxy import restore_system_proxy
        from proxycombo.relays import stop_relays
        try:
            restore_system_proxy()
        except Exception:
            pass
        stop_relays()

if __name__ == "__main__":
    if "--build" in sys.argv:
        from proxycombo.build import build_exe
        sys.exit(0 if build_exe() else 1)
    main_entry()