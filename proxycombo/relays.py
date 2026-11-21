import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import zipfile
import psutil
import requests
from .config import (
    GOST_EXE, SINGBOX_EXE, SINGBOX_CONFIG, SINGBOX_VERSION,
    LOCAL_PORT, CREATE_NO_WINDOW,
)
from .logging_utils import dbg

GOST_PROCESS = {"proc": None}
SINGBOX_PROCESS = {"proc": None}

_STARTUPINFO = subprocess.STARTUPINFO()
_STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
_STARTUPINFO.wShowWindow = 0

def _popen_hidden(*args, **kwargs):
    kwargs.setdefault("shell", False)
    kwargs.setdefault("stdout", subprocess.DEVNULL)
    kwargs.setdefault("stderr", subprocess.DEVNULL)
    kwargs.setdefault("stdin", subprocess.DEVNULL)
    kwargs.setdefault("creationflags", CREATE_NO_WINDOW)
    kwargs.setdefault("startupinfo", _STARTUPINFO)
    return subprocess.Popen(*args, **kwargs)

def _run_hidden(*args, **kwargs):
    kwargs.setdefault("shell", False)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("creationflags", CREATE_NO_WINDOW)
    kwargs.setdefault("startupinfo", _STARTUPINFO)
    return subprocess.run(*args, **kwargs)

def kill_all_process(name: str):
    try:
        for p in psutil.process_iter(["name"]):
            try:
                if p.info["name"] and p.info["name"].lower() == name.lower():
                    p.kill()
            except Exception:
                pass
    except Exception:
        pass

def is_port_open(host, port, timeout=1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, OSError):
        return False


def get_browser_processes(browser: str = "chrome"):
    try:
        from .config import BROWSERS
        names = set(BROWSERS.get(browser, {}).get("processes", []))
    except Exception:
        names = {"chrome.exe"}
    procs = []
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info["name"] or "").lower()
            if name in names:
                procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return procs

def get_chrome_processes():
    return get_browser_processes("chrome")

    procs = []
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == "chrome.exe":
                procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return procs

def _download_and_extract(urls, target, exe_marker, log=None):
    for url in urls:
        try:
            r = requests.get(url, timeout=120, stream=True, allow_redirects=True)
            if r.status_code != 200:
                continue
            tmp_zip = os.path.join(tempfile.gettempdir(), os.path.basename(target) + ".zip")
            with open(tmp_zip, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            with zipfile.ZipFile(tmp_zip, "r") as z:
                for name in z.namelist():
                    if name.lower().endswith(exe_marker):
                        z.extract(name, os.path.dirname(target))
                        extracted = os.path.join(os.path.dirname(target), name)
                        if os.path.exists(extracted) and extracted != target:
                            try:
                                os.replace(extracted, target)
                            except Exception:
                                pass
                        break
            try:
                os.remove(tmp_zip)
            except Exception:
                pass
            if os.path.exists(target):
                return True
        except Exception as e:
            dbg(f"download error {url}: {e}")
    return False

def install_gost(log=None):
    if os.path.exists(GOST_EXE):
        return True
    if log:
        log("📦 Скачиваю gost.exe...", "step")
    arch = "amd64" if sys.maxsize > 2 ** 32 else "386"
    urls = [
        f"https://github.com/go-gost/gost/releases/download/v3.0.0/gost-windows-{arch}-v3.0.0.zip",
        f"https://github.com/ginuerzh/gost/releases/download/v2.11.5/gost-windows-{arch}-2.11.5.zip",
    ]
    return _download_and_extract(urls, GOST_EXE, ".exe", log)

def install_singbox(log=None):
    if os.path.exists(SINGBOX_EXE):
        return True
    if log:
        log("📦 Скачиваю sing-box.exe...", "step")
    arch = "amd64" if sys.maxsize > 2 ** 32 else "386"
    zip_name = f"sing-box-{SINGBOX_VERSION}-windows-{arch}.zip"
    urls = [
        f"https://github.com/SagerNet/sing-box/releases/download/v{SINGBOX_VERSION}/{zip_name}",
        f"https://ghproxy.com/https://github.com/SagerNet/sing-box/releases/download/v{SINGBOX_VERSION}/{zip_name}",
    ]
    return _download_and_extract(urls, SINGBOX_EXE, "sing-box.exe", log)

def _wait_port(proc, log, timeout=10.0):
    elapsed = 0.0
    while elapsed < timeout:
        time.sleep(0.3)
        elapsed += 0.3
        if proc.poll() is not None:
            log("❌ Процесс релея упал", "error")
            return False
        if is_port_open("127.0.0.1", LOCAL_PORT, timeout=1.0):
            log(f"✅ Порт {LOCAL_PORT} открыт", "success")
            return True
    log("❌ Порт не открылся", "error")
    return False

def start_gost(proxy: dict, log) -> bool:
    if not os.path.exists(GOST_EXE):
        log("❌ gost.exe не найден", "error")
        return False
    kill_all_process("gost.exe")
    time.sleep(0.3)
    host, port = proxy["host"], proxy["port"]
    user, pwd = proxy["username"], proxy["password"]
    scheme = proxy.get("scheme", "socks5").lower()
    if scheme.startswith("sock"):
        scheme = "socks5"
    upstream = (f"{scheme}://{user}:{pwd}@{host}:{port}" if user
                else f"{scheme}://{host}:{port}")
    try:
        proc = _popen_hidden(
            [GOST_EXE,
             "-L", f"socks5://127.0.0.1:{LOCAL_PORT}",
             "-L", f"http://127.0.0.1:{LOCAL_PORT + 1}",
             "-F", upstream]
        )
        GOST_PROCESS["proc"] = proc
        log(f"🚀 gost → {scheme}://{host}:{port}", "step")
        return _wait_port(proc, log)
    except Exception as e:
        log(f"❌ Ошибка gost: {e}", "error")
        return False

def start_singbox(proxy: dict, log) -> bool:
    if not os.path.exists(SINGBOX_EXE):
        log("❌ sing-box.exe не найден", "error")
        return False
    kill_all_process("sing-box.exe")
    time.sleep(0.3)
    host, port = proxy["host"], proxy["port"]
    user, pwd = proxy["username"], proxy["password"]
    scheme = proxy.get("scheme", "socks5").lower()
    outbound_type = "http" if scheme.startswith("http") else "socks"

    outbound = {"type": outbound_type, "tag": "proxy-out",
                "server": host, "server_port": int(port)}
    if user:
        outbound["username"] = user
        outbound["password"] = pwd
    if outbound_type == "socks":
        outbound["version"] = "5"

    config = {
        "log": {"level": "warn"},
        "inbounds": [{"type": "mixed", "tag": "mixed-in",
                      "listen": "127.0.0.1", "listen_port": LOCAL_PORT}],
        "outbounds": [outbound],
    }

    try:
        with open(SINGBOX_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        check = _run_hidden([SINGBOX_EXE, "check", "-c", SINGBOX_CONFIG],
                            text=True, timeout=10)
        if check.returncode != 0:
            log(f"❌ sing-box check: {check.stderr[:200]}", "error")
            return False
        proc = _popen_hidden([SINGBOX_EXE, "run", "-c", SINGBOX_CONFIG])
        SINGBOX_PROCESS["proc"] = proc
        log(f"🚀 sing-box → {scheme}://{host}:{port}", "step")
        return _wait_port(proc, log)
    except Exception as e:
        log(f"❌ Ошибка sing-box: {e}", "error")
        return False

def stop_relays(log=None):
    for name in ("gost.exe", "sing-box.exe"):
        kill_all_process(name)
    GOST_PROCESS["proc"] = None
    SINGBOX_PROCESS["proc"] = None
    if log:
        log("🛑 Релеи остановлены", "info")

def check_relay_raw_socks(timeout=12):
    try:
        import socks
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, "127.0.0.1", LOCAL_PORT)
        s.settimeout(timeout)
        s.connect(("api.ipify.org", 80))
        s.sendall(b"GET /?format=json HTTP/1.1\r\nHost: api.ipify.org\r\n"
                  b"User-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n")
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        text = data.decode("utf-8", errors="ignore")
        if '"ip":"' in text:
            return True, text.split('"ip":"')[1].split('"')[0]
        return False, "нет IP"
    except Exception as e:
        return False, str(e)[:100]

def check_relay_http(timeout=12):
    try:
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({
            "http": f"http://127.0.0.1:{LOCAL_PORT}",
            "https": f"http://127.0.0.1:{LOCAL_PORT}",
        })
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request("http://api.ipify.org/?format=json",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
            if '"ip":"' in data:
                return True, data.split('"ip":"')[1].split('"')[0]
            return True, data[:60]
    except Exception as e:
        return False, str(e)[:100]

def check_relay(timeout=12):
    ok, res = check_relay_http(timeout)
    if ok:
        return ok, res
    ok2, res2 = check_relay_raw_socks(timeout)
    if ok2:
        return ok2, res2
    return False, f"HTTP: {res} | SOCKS: {res2}"