import urllib.error
import urllib.request

def trigger_pool_rotation(proxy_pool: list, current_idx: int, log=None):
    if not proxy_pool: return False, None, -1
    next_idx = (current_idx + 1) % len(proxy_pool)
    if log: log(f"🔄 Смена из пула: индекс {next_idx}", "info")
    return True, proxy_pool[next_idx], next_idx

def trigger_rotation(url: str, log=None):
    if not url:
        return False, "URL пустой", 0

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    attempts = [
        ("GET", url, {"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}),
        ("GET", url.replace("https://", "http://"), {"User-Agent": "Mozilla/5.0"}),
    ]
    last_err, last_code = "unknown", 0
    for method, target_url, headers in attempts:
        try:
            if log:
                log(f"🔄 {method} {target_url[:70]}...", "info")
            req = urllib.request.Request(target_url, method=method, headers=headers)
            with opener.open(req, timeout=30) as resp:
                code = resp.status
                body = resp.read().decode("utf-8", errors="ignore")[:300]
                if 200 <= code < 300:
                    return True, f"код {code}: {body[:100]}", code
                last_err, last_code = f"код {code}: {body[:100]}", code
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="ignore")[:300]
            except Exception:
                pass
            if e.code == 429:
                if log:
                    log("⏳ 429: ротация уже идёт", "warn")
                return True, "ротация уже в процессе (429)", 429
            last_err, last_code = f"HTTP {e.code}: {body[:120]}", e.code
        except Exception as e:
            last_err = str(e)[:120]
            if log:
                log(f"⚠️ {last_err}", "warn")
            continue
    return False, last_err, last_code