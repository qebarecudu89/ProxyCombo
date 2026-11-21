
def test_proxy_direct(proxy: dict, timeout=4) -> tuple:
    """Быстрая проверка прокси без запуска релея."""
    try:
        import socks
        s = socks.socksocket()
        scheme = socks.SOCKS5 if proxy["scheme"] == "socks5" else socks.HTTP
        s.set_proxy(scheme, proxy["host"], int(proxy["port"]), 
                    username=proxy.get("username"), password=proxy.get("password"))
        s.settimeout(timeout)
        s.connect(("api.ipify.org", 80))
        s.sendall(b"GET /?format=json HTTP/1.1\r\nHost: api.ipify.org\r\nConnection: close\r\n\r\n")
        data = s.recv(1024).decode("utf-8", errors="ignore")
        s.close()
        if '"ip":"' in data:
            return True, data.split('"ip":"')[1].split('"')[0]
        return False, "Нет IP в ответе"
    except Exception as e:
        return False, str(e)[:50]
