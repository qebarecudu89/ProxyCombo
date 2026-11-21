import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def replace_in_file(rel_path, old, new):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path): return False
    with open(path, "r", encoding="utf-8") as f: content = f.read()
    if old not in content: return False
    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f: f.write(content)
    return True

def write_file(rel_path, content):
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f: f.write(content)

def main():
    print("🔧 Устанавливаю глобальное обновление v1.2.0...")

    # 1. VERSION
    replace_in_file("version.py", 'VERSION = "1.1.0"', 'VERSION = "1.2.0"')

    # 2. CONFIG.PY (Добавляем флаги защиты и настройки обновлений)
    cfg_old = 'CREATE_NO_WINDOW = 0x08000000'
    cfg_new = '''CREATE_NO_WINDOW = 0x08000000

# ---- Обновления ----
GITHUB_REPO = "yourname/proxycombo"
CURRENT_VERSION = "1.2.0"

# ---- Защита ----
SPOOF_TIMEZONE = False
BLOCK_WEBRTC = True

# ---- Профили и Прокси ----
PROFILES_FILE = os.path.join(BASE_DIR, "profiles.json")
PROXY_POOL_FILE = os.path.join(BASE_DIR, "proxy_pool.txt")
AUTO_ROTATE_MINUTES = 0 # 0 = выкл
'''
    replace_in_file("proxycombo/config.py", cfg_old, cfg_new)

    # 3. STATE.PY (Добавляем список прокси)
    state_old = '''        "rotation_url": "",'''
    state_new = '''        "rotation_url": "",
        "proxy_pool": [],
        "auto_rotate_mins": 0,
        "webrtc_block": True,'''
    replace_in_file("proxycombo/state.py", state_old, state_new)

    # 4. RELAYS.PY (Чекер + Запуск с пула)
    relays_code = '''
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
        s.sendall(b"GET /?format=json HTTP/1.1\\r\\nHost: api.ipify.org\\r\\nConnection: close\\r\\n\\r\\n")
        data = s.recv(1024).decode("utf-8", errors="ignore")
        s.close()
        if '"ip":"' in data:
            return True, data.split('"ip":"')[1].split('"')[0]
        return False, "Нет IP в ответе"
    except Exception as e:
        return False, str(e)[:50]
'''
    write_file("proxycombo/relay_utils.py", relays_code)

    # 5. ROTATION.PY (Пул прокси)
    rotation_old = 'def trigger_rotation(url: str, log=None):'
    rotation_new = '''def trigger_pool_rotation(proxy_pool: list, current_idx: int, log=None):
    if not proxy_pool: return False, None, -1
    next_idx = (current_idx + 1) % len(proxy_pool)
    if log: log(f"🔄 Смена из пула: индекс {next_idx}", "info")
    return True, proxy_pool[next_idx], next_idx

def trigger_rotation(url: str, log=None):'''
    replace_in_file("proxycombo/rotation.py", rotation_old, rotation_new)

    # 6. UPDATER.PY (Автообновление)
    updater_code = '''
import urllib.request
import json
import os
import subprocess
import sys
from .config import GITHUB_REPO, CURRENT_VERSION
from .logging_utils import file_log, dbg

def check_for_updates():
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "ProxyCombo"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            latest = data.get("tag_name", "").lstrip("v")
            if latest and latest != CURRENT_VERSION:
                return latest, data.get("assets", [])
    except Exception as e:
        dbg(f"Update check failed: {e}")
    return None, []

def apply_update(asset_url):
    try:
        patch_path = os.path.join(os.path.dirname(__file__), "..", "patches", "update.patch")
        urllib.request.urlretrieve(asset_url, patch_path)
        subprocess.run([sys.executable, "patches/apply_patch.py", "patches/update.patch"], check=True)
        return True
    except Exception as e:
        file_log(f"Update apply failed: {e}")
        return False
'''
    write_file("proxycombo/updater.py", updater_code)

    # 7. APP.PY (Главные изменения)
    # 7.1 Импорты
    app_imports_old = '''from .ui.window import build_title_bar, build_status_bar, build_action_bar'''
    app_imports_new = '''from .ui.window import build_title_bar, build_status_bar, build_action_bar
from .relay_utils import test_proxy_direct
from .rotation import trigger_pool_rotation
from .updater import check_for_updates, apply_update'''
    replace_in_file("proxycombo/app.py", app_imports_old, app_imports_new)

    # 7.2 Подгрузка профилей
    app_state_old = '''    state = state_mod.load_state()'''
    app_state_new = '''    state = state_mod.load_state()
    
    # Загрузка пула
    pool_state = {"list": state.get("proxy_pool", []), "idx": -1}
    if not pool_state["list"]:
        try:
            with open(C.PROXY_POOL_FILE, "r", encoding="utf-8") as f:
                pool_state["list"] = [l.strip() for l in f if l.strip()]
        except Exception: pass'''
    replace_in_file("proxycombo/app.py", app_state_old, app_state_new)

    # 7.3 UI: Настройка защиты и Авто-ротации
    app_switch_old = '''    sys_proxy_switch = ft.Switch('''
    app_switch_new = '''    webrtc_switch = ft.Switch(value=state.get("webrtc_block", True), active_color=C.SUCCESS)
    auto_rotate_input = ft.TextField(value=str(state.get("auto_rotate_mins", 0)), width=60, height=40, text_size=11, text_align=ft.TextAlign.CENTER)
    
    def on_webrtc_change(e):
        state["webrtc_block"] = e.control.value
        state_mod.save_state(state)

    webrtc_switch.on_change = on_webrtc_change

    # ---- Проверка прокси ----
    async def on_test_proxy(e):
        proxy = current_proxy_from_ui()
        if not proxy:
            log("❌ Прокси не задан", "error"); return
        log("🔍 Проверяю прокси напрямую...", "step")
        loop = asyncio.get_event_loop()
        ok, msg = await loop.run_in_executor(None, test_proxy_direct, proxy)
        if ok: log(f"✅ Прокси рабочий! IP: {msg}", "success")
        else: log(f"❌ Прокси мертв: {msg}", "error")

    test_proxy_btn = ft.Container(
        content=ft.Text("Проверить прокси", size=11, color=C.CYAN),
        padding=8, border_radius=8, bgcolor=C.BG_INPUT,
        on_click=lambda e: asyncio.create_task(on_test_proxy(e))
    )

    sys_proxy_switch = ft.Switch('''
    replace_in_file("proxycombo/app.py", app_switch_old, app_switch_new)

    # 7.4 Логика: Защита WebRTC + Timezone
    app_args_old = '''            chrome_args = [
                f"--user-data-dir={temp_profile}", proxy_arg,'''
    app_args_new = '''            chrome_args = [
                f"--user-data-dir={temp_profile}", proxy_arg,'''
    
    app_args_append_old = '''                "--disable-gpu-shader-disk-cache",
            ]
            hooks.run("before_chrome_launch", chrome_args, urls, log)'''
    app_args_append_new = '''                "--disable-gpu-shader-disk-cache",
            ]
            if state.get("webrtc_block", True):
                chrome_args.append("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
            if C.SPOOF_TIMEZONE:
                chrome_args.append('--js-flags="--timezone=\\'Europe/London\\'"')
            
            hooks.run("before_chrome_launch", chrome_args, urls, log)'''
    replace_in_file("proxycombo/app.py", app_args_append_old, app_args_append_new)

    # 7.5 Логика: Пул прокси при ротации
    app_rot_old = '''    async def manual_rotate():
        if busy["value"]:'''
    app_rot_new = '''    async def auto_rotate_monitor():
        while True:
            await asyncio.sleep(60)
            mins = int(state.get("auto_rotate_mins", 0))
            if mins > 0 and not busy["value"]:
                elapsed = time.time() - last_rotation_ts["value"]
                if elapsed > mins * 60:
                    await manual_rotate()

    async def manual_rotate():
        if busy["value"]:'''
    replace_in_file("proxycombo/app.py", app_rot_old, app_rot_new)

    app_rot_logic_old = '''            rot_url = rotation_url_input.value.strip()
            if not rot_url:
                log("❌ URL ротации не задан", "error")
                return'''
    app_rot_logic_new = '''            rot_url = rotation_url_input.value.strip()
            
            # Если есть пул, используем его
            if pool_state["list"]:
                ok, new_proxy, next_idx = trigger_pool_rotation(pool_state["list"], pool_state["idx"], log)
                if ok:
                    pool_state["idx"] = next_idx
                    proxy_host_input.value = new_proxy.split(":")[0]
                    proxy_port_input.value = new_proxy.split(":")[1]
                    proxy_user_input.value = ""
                    proxy_pass_input.value = ""
                    save_fields()
                    log(f"✅ Новый прокси: {proxy_host_input.value}:{proxy_port_input.value}", "success")
                    # перезапуск релея
                    await loop.run_in_executor(None, relays.stop_relays)
                    await loop.run_in_executor(None, relays.start_singbox, current_proxy_from_ui(), log)
                    await refresh_ip_async()
                    return
            elif not rot_url:
                log("❌ Нет ни пула, ни URL ротации", "error")
                return'''
    replace_in_file("proxycombo/app.py", app_rot_logic_old, app_rot_logic_new)

    # 7.6 Обновления UI (ctx)
    app_ctx_old = '''        "browser_dropdown": browser_dropdown,'''
    app_ctx_new = '''        "webrtc_switch": webrtc_switch,
        "auto_rotate_input": auto_rotate_input,
        "test_proxy_btn": test_proxy_btn,
        "browser_dropdown": browser_dropdown,'''
    replace_in_file("proxycombo/app.py", app_ctx_old, app_ctx_new)

    # 7.7 Обновления: Запуск корутины авто-ротации
    app_task_old = '''    page.run_task(speed_monitor)'''
    app_task_new = '''    page.run_task(speed_monitor)
    page.run_task(auto_rotate_monitor)'''
    replace_in_file("proxycombo/app.py", app_task_old, app_task_new)
    
    # 7.8 Добавление кнопки "Проверить обновления" при старте
    app_startup_old = '''    update_status_from_state()

    log("👋 Proxy Combo готов", "info")'''
    app_startup_new = '''    update_status_from_state()

    async def check_updates_on_start():
        latest, assets = await asyncio.get_event_loop().run_in_executor(None, check_for_updates)
        if latest:
            log(f"🚀 Доступно обновление: v{latest} (текущая: v{C.CURRENT_VERSION})", "warn")
            log("💡 Скачайте новый патч с GitHub и примените его.", "info")
    
    page.run_task(check_updates_on_start)

    log("👋 Proxy Combo готов", "info")'''
    replace_in_file("proxycombo/app.py", app_startup_old, app_startup_new)

    # 8. UI TABS (Добавляем новые элементы)
    tabs_proxy_old = '''                        ft.Row([proxy_user_input, proxy_pass_input],
                               spacing=8),'''
    tabs_proxy_new = '''                        ft.Row([proxy_user_input, proxy_pass_input],
                               spacing=8),
                        ft.Container(height=8),
                        ft.Row(
                            [
                                ctx["test_proxy_btn"],
                                ft.Container(expand=True),
                                ft.Text("WebRTC Leak", size=10, color=C.TEXT_DIM),
                                ctx["webrtc_switch"],
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),'''
    replace_in_file("proxycombo/ui/tabs.py", tabs_proxy_old, tabs_proxy_new)

    tabs_rot_old = '''                        ft.Text("Ротация 1 раз в 2 минуты. На время ротации "
                                "системный прокси временно отключается",
                                size=10, color=C.SUBTEXT),'''
    tabs_rot_new = '''                        ft.Text("При наличии пула — переключение по списку. Иначе — по URL.",
                                size=10, color=C.SUBTEXT),
                        ft.Container(height=8),
                        ft.Row(
                            [
                                ft.Text("Авто-ротация (мин):", size=11, color=C.TEXT),
                                ctx["auto_rotate_input"],
                                ft.Text("0 = выкл", size=10, color=C.SUBTEXT),
                            ],
                            spacing=8,
                        ),'''
    replace_in_file("proxycombo/ui/tabs.py", tabs_rot_old, tabs_rot_new)

    print("✅ Патч v1.2.0 успешно установлен!")
    print("💡 Проверь: python main.py --debug")

if __name__ == "__main__":
    main()