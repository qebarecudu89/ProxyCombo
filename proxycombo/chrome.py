import os
import shutil
import time

from .config import (
    TEMP_PROFILE, TEMP_PROFILE_YANDEX, BROWSERS, DEFAULT_BROWSER,
)
from .relays import _run_hidden, get_browser_processes

def _browser_cfg(browser: str) -> dict:
    return BROWSERS.get(browser) or BROWSERS[DEFAULT_BROWSER]

def get_browser_temp_profile(browser: str) -> str:
    return TEMP_PROFILE_YANDEX if browser == "yandex" else TEMP_PROFILE

def find_browser_exe(browser: str = None):
    if browser is None:
        for key in BROWSERS:
            p = find_browser_exe(key)
            if p:
                return p
        return None

    cfg = _browser_cfg(browser)
    for p in cfg.get("paths", []):
        p_expanded = os.path.expandvars(p)
        if os.path.exists(p_expanded):
            return p_expanded

    try:
        import winreg
        reg_path = cfg.get("registry")
        if not reg_path:
            return None
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(hive, reg_path) as k:
                    val, _ = winreg.QueryValueEx(k, None)
                    if val and os.path.exists(val):
                        return val
            except FileNotFoundError:
                pass
    except Exception:
        pass
    return None

def find_chrome_exe():
    return find_browser_exe("chrome")

def get_user_data_path(browser: str = None) -> str:
    if browser is None:
        browser = DEFAULT_BROWSER
    cfg = _browser_cfg(browser)
    return os.path.expandvars(cfg["user_data"])

def kill_all_browser(browser: str = None, log=None) -> bool:
    if browser is None:
        browser = DEFAULT_BROWSER
    cfg = _browser_cfg(browser)
    title = cfg.get("title", browser)
    procs = get_browser_processes(browser)
    if not procs:
        if log:
            log(f"✅ {title} не запущен", "success")
        return True
    if log:
        log(f"🔪 Убиваю {len(procs)} процессов {title}", "step")
    for p in procs:
        try:
            p.kill()
        except Exception:
            pass
    time.sleep(1)
    for exe in cfg.get("processes", []):
        _run_hidden(["taskkill", "/F", "/IM", exe, "/T"], shell=True)
    for _ in range(6):
        time.sleep(1)
        if not get_browser_processes(browser):
            break
    remaining = get_browser_processes(browser)
    if remaining:
        if log:
            log(f"⚠️ Остались процессы {title}: {len(remaining)}", "warn")
        return False
    if log:
        log(f"✅ Все процессы {title} убиты", "success")
    return True

def kill_all_chrome(log=None):
    return kill_all_browser("chrome", log)

def full_clean(user_data, log, progress_cb=None):
    if not os.path.exists(user_data):
        log(f"❌ Папка не найдена: {user_data}", "error")
        return False
    all_items = [os.path.join(user_data, item) for item in os.listdir(user_data)]
    keep = {"Local State"}
    total = len(all_items)
    deleted, errors = 0, 0
    for idx, path in enumerate(all_items):
        if os.path.basename(path) in keep:
            if progress_cb:
                progress_cb(int((idx + 1) / total * 100))
            continue
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
            deleted += 1
        except Exception:
            errors += 1
        if progress_cb:
            progress_cb(int((idx + 1) / total * 100))
    log(f"✅ Очищено: удалено {deleted}, ошибок {errors}", "success")
    return True

def prepare_temp_profile(browser: str = None, log=None) -> bool:
    if browser is None:
        browser = DEFAULT_BROWSER
    profile = get_browser_temp_profile(browser)
    try:
        if os.path.exists(profile):
            shutil.rmtree(profile, ignore_errors=True)
        os.makedirs(profile, exist_ok=True)
        return True
    except Exception:
        return False
