import sys
import time
import traceback

DEBUG = "--debug" in sys.argv

def dbg(msg: str):
    if DEBUG:
        print(f"[DEBUG {time.strftime('%H:%M:%S')}] {msg}", flush=True)

def file_log(msg: str):
    from .config import LOG_FILE
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def fatal(exc: Exception):
    file_log(f"КРИТИЧЕСКАЯ: {exc}\n{traceback.format_exc()}")