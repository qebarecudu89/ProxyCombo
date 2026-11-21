import json
import os
from .config import STATE_FILE, URLS_FILE

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "mode": "singbox",
        "browser": "chrome",
        "rotation_url": "",
        "proxy_pool": [],
        "auto_rotate_mins": 0,
        "webrtc_block": True,
        "proxy_host": "",
        "proxy_port": "",
        "proxy_type": "socks5",
        "proxy_user": "",
        "proxy_pass": "",
    }

def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_urls() -> list:
    if not os.path.exists(URLS_FILE):
        return []
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]

def save_urls(urls: list):
    with open(URLS_FILE, "w", encoding="utf-8") as f:
        f.write("# Список сайтов для автооткрытия\n\n")
        for u in urls:
            f.write(u + "\n")

def normalize_url(url: str):
    url = url.strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://", "chrome://",
                           "file://", "ftp://")):
        url = "https://" + url
    return url