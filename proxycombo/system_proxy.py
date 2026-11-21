import ctypes
import json
import os
from .config import SYS_PROXY_BACKUP, LOCAL_PORT
from .logging_utils import dbg
from .relays import is_port_open

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

def _refresh_internet_settings():
    try:
        f = ctypes.windll.Wininet.InternetSetOptionW
        f(0, 39, 0, 0)
        f(0, 37, 0, 0)
        return True
    except Exception as e:
        dbg(f"refresh_internet_settings: {e}")
        return False

def _read_system_proxy():
    result = {"enabled": False, "server": "", "override": ""}
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                            winreg.KEY_READ) as key:
            for name, field in (("ProxyEnable", "enabled"),
                                ("ProxyServer", "server"),
                                ("ProxyOverride", "override")):
                try:
                    val, _ = winreg.QueryValueEx(key, name)
                    result[field] = bool(val) if field == "enabled" else (val or "")
                except FileNotFoundError:
                    pass
    except Exception as e:
        dbg(f"_read_system_proxy: {e}")
    return result

def _write_system_proxy(enabled: bool, server: str = "", override: str = ""):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                            winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1 if enabled else 0)
            if server:
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, server)
            if override:
                winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, override)
        _refresh_internet_settings()
        return True
    except Exception as e:
        dbg(f"_write_system_proxy: {e}")
        return False

def _backup_system_proxy():
    try:
        with open(SYS_PROXY_BACKUP, "w", encoding="utf-8") as f:
            json.dump(_read_system_proxy(), f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def restore_system_proxy(log=None):
    if not os.path.exists(SYS_PROXY_BACKUP):
        cur = _read_system_proxy()
        if cur["enabled"] and "127.0.0.1" in cur["server"]:
            _write_system_proxy(False)
        return
    try:
        with open(SYS_PROXY_BACKUP, "r", encoding="utf-8") as f:
            data = json.load(f)
        _write_system_proxy(
            enabled=data.get("enabled", False),
            server=data.get("server", ""),
            override=data.get("override", ""),
        )
        os.remove(SYS_PROXY_BACKUP)
        if log:
            log("♻️ Системный прокси восстановлен", "info")
    except Exception as e:
        dbg(f"restore error: {e}")

_restore_system_proxy = restore_system_proxy

def reset_dead_local_proxy_on_startup(log=None):
    cur = _read_system_proxy()
    if not cur["enabled"]:
        return False
    server = cur["server"].lower()
    is_ours = ("127.0.0.1:1080" in server) or ("localhost:1080" in server)
    if not is_ours:
        return False
    if not is_port_open("127.0.0.1", LOCAL_PORT, timeout=0.5):
        _write_system_proxy(False)
        if log:
            log("⚠️ Сброшен 'залипший' системный прокси", "warn")
        return True
    return False

def set_system_proxy(host: str, port: int, log=None) -> bool:
    if not os.path.exists(SYS_PROXY_BACKUP):
        _backup_system_proxy()
    try:
        proxy_str = f"{host}:{port}"
        ok = _write_system_proxy(
            enabled=True, server=proxy_str,
            override="<-loopback>;localhost;127.0.0.1",
        )
        if ok and log:
            log(f"🌐 Системный прокси включён: {proxy_str}", "success")
        return ok
    except Exception as e:
        if log:
            log(f"❌ Ошибка системного прокси: {e}", "error")
        return False

def clear_system_proxy(log=None) -> bool:
    ok = _write_system_proxy(False)
    if ok and log:
        log("🌐 Системный прокси выключен", "success")
    return ok

def is_system_proxy_enabled() -> bool:
    return _read_system_proxy().get("enabled", False)