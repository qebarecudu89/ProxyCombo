import socket
import threading
import time
import psutil
from .config import LOCAL_PORT
from .relays import is_port_open, check_relay

_net_stat_lock = threading.Lock()
_net_last = {"ts": 0.0, "bytes_sent": 0, "bytes_recv": 0}

def calc_speed():
    try:
        io = psutil.net_io_counters()
        sent, recv = io.bytes_sent, io.bytes_recv
    except Exception:
        return 0.0, 0.0
    now = time.time()
    with _net_stat_lock:
        last = _net_last
        if last["ts"] == 0:
            _net_last.update({"ts": now, "bytes_sent": sent, "bytes_recv": recv})
            return 0.0, 0.0
        dt = now - last["ts"]
        if dt <= 0:
            return 0.0, 0.0
        d_sent = sent - last["bytes_sent"]
        d_recv = recv - last["bytes_recv"]
        _net_last.update({"ts": now, "bytes_sent": sent, "bytes_recv": recv})
        return max(0.0, d_sent / dt / 1024), max(0.0, d_recv / dt / 1024)

def measure_ping(timeout=5):
    try:
        start = time.time()
        if is_port_open("127.0.0.1", LOCAL_PORT, timeout=1.0):
            import socks
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, "127.0.0.1", LOCAL_PORT)
            s.settimeout(timeout)
            s.connect(("api.ipify.org", 443))
            ping_ms = (time.time() - start) * 1000
            s.close()
            return ping_ms
        s = socket.socket()
        s.settimeout(timeout)
        s.connect(("api.ipify.org", 443))
        ping_ms = (time.time() - start) * 1000
        s.close()
        return ping_ms
    except Exception:
        return -1

def get_current_ip():
    if is_port_open("127.0.0.1", LOCAL_PORT, timeout=0.5):
        ok, ip = check_relay(timeout=8)
        if ok:
            return ip
    try:
        import urllib.request
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request("https://api.ipify.org/?format=json",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=8) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
            if '"ip":"' in data:
                return data.split('"ip":"')[1].split('"')[0]
    except Exception:
        pass
    return "?"