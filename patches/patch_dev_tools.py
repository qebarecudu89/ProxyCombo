import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write_file(rel_path, content):
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f: 
        f.write(content)

def main():
    print("🚀 Установка панели разработчика (DevTools)...")

    # 1. Обновляем config.py
    c_path = os.path.join(ROOT, "proxycombo", "config.py")
    with open(c_path, "r", encoding="utf-8") as f: c_content = f.read()
    
    if "DEV_MODE" not in c_content:
        c_content += '\n\n# Режим разработчика\nDEV_MODE = True\n'
    with open(c_path, "w", encoding="utf-8", newline="\n") as f: f.write(c_content)

    # 2. Создаем dev_tools.py (логика работы)
    dev_code = '''import os
import sys
import subprocess
import webbrowser
import urllib.request
import json
from .config import BASE_DIR, GITHUB_REPO, GITHUB_TOKEN, CURRENT_VERSION

def build_exe():
    try:
        # Запускаем сборку через subprocess
        p = subprocess.Popen([sys.executable, "main.py", "--build"], cwd=BASE_DIR)
        p.wait()
        return True, "Сборка завершена. Файл в папке dist/ProxyCombo.exe"
    except Exception as e:
        return False, str(e)

def apply_local_patch(filepath):
    try:
        p = subprocess.run([sys.executable, "patches/apply_patch.py", filepath], 
                           cwd=BASE_DIR, capture_output=True, text=True)
        if p.returncode == 0:
            return True, "Патч успешно применён! Перезапустите программу."
        return False, p.stderr or p.stdout
    except Exception as e:
        return False, str(e)

def publish_release(version, token, exe_path):
    if not token:
        return False, "Токен не указан"
    if not os.path.exists(exe_path):
        return False, "Файл EXE не найден. Сначала соберите проект."
        
    try:
        # 1. Создаем релиз через API GitHub
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ProxyCombo-Dev"
        }
        data = json.dumps({
            "tag_name": f"v{version}",
            "name": f"Release v{version}",
            "body": f"Автоматический релиз от ProxyCombo DevTools.",
            "draft": False,
            "prerelease": False
        }).encode("utf-8")
        
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read().decode())
            upload_url = resp["upload_url"].split("{")[0]
            
        # 2. Загружаем EXE
        with open(exe_path, "rb") as f:
            exe_data = f.read()
            
        upload_headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/octet-stream",
            "User-Agent": "ProxyCombo-Dev"
        }
        upload_url = f"{upload_url}?name=ProxyCombo.exe"
        req2 = urllib.request.Request(upload_url, data=exe_data, headers=upload_headers, method="POST")
        
        with urllib.request.urlopen(req2) as r2:
            pass
            
        return True, f"Релиз v{version} успешно опубликован на GitHub!"
    except Exception as e:
        return False, str(e)
'''
    write_file("proxycombo/dev_tools.py", dev_code)

    # 3. Пересоздаем app.py с нуля (чтобы убрать весь мусор от прошлых патчей)
    app_code = '''import asyncio
import os
import random
import time
import traceback
import flet as ft

from . import config as C
from . import state as state_mod
from . import hooks
from .logging_utils import file_log, dbg
from . import relays
from .rotation import trigger_rotation, trigger_pool_rotation
from .chrome import (find_browser_exe, get_user_data_path, kill_all_browser,
                     kill_all_chrome, full_clean, prepare_temp_profile,
                     get_browser_temp_profile)
from .net_monitor import calc_speed, measure_ping, get_current_ip
from .system_proxy import (is_system_proxy_enabled, set_system_proxy,
                           clear_system_proxy,
                           reset_dead_local_proxy_on_startup)
from .ui.theme import page_ref, gradient_btn
from .ui.widgets import make_field, make_tab_btn, switch_tab
from .ui.tabs import build_tabs
from .ui.window import build_title_bar, build_status_bar, build_action_bar
from .relay_utils import test_proxy_direct
from .updater import check_for_updates, download_and_update
from . import dev_tools

async def main(page: ft.Page):
    page_ref["page"] = page
    page.title = "Proxy Combo"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = C.BG_DEEP
    page.padding = 0
    page.spacing = 0
    try:
        page.window.frameless = True
        page.window.resizable = True
        page.window.width = 560
        page.window.height = 780
        page.window.min_width = 480
        page.window.min_height = 560
        page.window.visible = True
    except Exception as e:
        dbg(f"window setup error: {e}")

    state = state_mod.load_state()
    
    pool_state = {"list": state.get("proxy_pool", []), "idx": -1}
    if not pool_state["list"]:
        try:
            with open(C.PROXY_POOL_FILE, "r", encoding="utf-8") as f:
                pool_state["list"] = [l.strip() for l in f if l.strip()]
        except Exception: pass

    busy = {"value": False}
    last_rotation_ts = {"value": 0.0}

    try:
        reset_dead_local_proxy_on_startup()
    except Exception:
        pass

    proxy_host_input = make_field("IP / Хост", expand=True)
    proxy_port_input = make_field("Порт", width=120)
    proxy_user_input = make_field("Логин", expand=True)
    proxy_pass_input = make_field("Пароль", password=True, expand=True)

    proxy_type_input = ft.Dropdown(
        label="Тип прокси", value="socks5",
        options=[ft.dropdown.Option("socks5", "SOCKS5"),
                 ft.dropdown.Option("http", "HTTP")],
        border_color=C.BORDER, focused_border_color=C.PURPLE, color=C.TEXT,
        bgcolor=C.BG_INPUT, border_radius=10, text_size=12, width=180,
    )

    rotation_url_input = ft.TextField(
        value="", label="URL ротации IP (из ЛК)",
        border_color=C.BORDER, focused_border_color=C.WARNING,
        color=C.TEXT, text_size=11, bgcolor=C.BG_INPUT, border_radius=10,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=12),
    )

    def save_fields(e=None):
        state["proxy_host"] = proxy_host_input.value.strip()
        state["proxy_port"] = proxy_port_input.value.strip()
        state["proxy_type"] = proxy_type_input.value
        state["proxy_user"] = proxy_user_input.value.strip()
        state["proxy_pass"] = proxy_pass_input.value or ""
        state["rotation_url"] = rotation_url_input.value.strip()
        state_mod.save_state(state)

    for fld in (proxy_host_input, proxy_port_input, proxy_user_input,
                proxy_pass_input, rotation_url_input):
        fld.on_change = save_fields
    proxy_type_input.on_change = save_fields

    proxy_host_input.value = state.get("proxy_host", "")
    proxy_port_input.value = state.get("proxy_port", "")
    proxy_user_input.value = state.get("proxy_user", "")
    proxy_pass_input.value = state.get("proxy_pass", "")
    proxy_type_input.value = state.get("proxy_type", "socks5")
    rotation_url_input.value = state.get("rotation_url", "")

    # ------- Браузер -------
    browser_state = {"value": state.get("browser", C.DEFAULT_BROWSER)}
    if browser_state["value"] not in C.BROWSERS:
        browser_state["value"] = C.DEFAULT_BROWSER

    browser_dropdown = ft.Dropdown(
        label="Браузер",
        value=browser_state["value"],
        options=[ft.dropdown.Option(k, v["title"]) for k, v in C.BROWSERS.items()],
        border_color=C.BORDER, focused_border_color=C.ORANGE, color=C.TEXT,
        bgcolor=C.BG_INPUT, border_radius=10, text_size=12, width=200,
    )

    def on_browser_change(e):
        browser_state["value"] = e.control.value
        state["browser"] = e.control.value
        state_mod.save_state(state)
        page.update()

    browser_dropdown.on_change = on_browser_change

    async def on_kill_browser(e=None):
        b = browser_state["value"]
        title = C.BROWSERS[b]["title"]
        log(f"🔪 Закрываю {title}...", "step")
        ok = await asyncio.get_event_loop().run_in_executor(None, kill_all_browser, b, log)
        if ok:
            log(f"✅ {title} закрыт", "success")

    browser_kill_btn = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.CLOSE, size=14, color=C.DANGER), ft.Text("Закрыть браузер", size=11, color=C.TEXT)], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        on_click=on_kill_browser, padding=ft.Padding.symmetric(vertical=8, horizontal=12), bgcolor=C.BG_INPUT,
        border=ft.Border.all(1, C.BORDER_SOFT), border_radius=10,
    )

    def current_proxy_from_ui():
        try:
            port = int(proxy_port_input.value.strip())
        except (ValueError, AttributeError):
            return None
        host = (proxy_host_input.value or "").strip()
        if not host:
            return None
        return {"host": host, "port": port, "scheme": proxy_type_input.value or "socks5",
                "username": (proxy_user_input.value or "").strip(), "password": proxy_pass_input.value or ""}

    status_dot = ft.Container(width=8, height=8, border_radius=4, bgcolor=C.SUBTEXT)
    status_text = ft.Text("Прямой интернет (прокси не задан)", size=11, color=C.SUBTEXT, weight=ft.FontWeight.W_600)
    ip_text = ft.Text("IP: —", size=11, color=C.CYAN, font_family="Consolas", weight=ft.FontWeight.W_700)

    log_list = ft.ListView(spacing=3, padding=ft.Padding.all(8), auto_scroll=True, expand=True)

    def log(msg, level="info"):
        colors = {"info": C.CYAN, "success": C.SUCCESS, "warn": C.WARNING, "error": C.DANGER, "step": C.PURPLE}
        icons = {"info": ft.Icons.INFO_OUTLINE, "success": ft.Icons.CHECK_CIRCLE_OUTLINE, "warn": ft.Icons.WARNING_AMBER, "error": ft.Icons.ERROR_OUTLINE, "step": ft.Icons.CHEVRON_RIGHT}
        c = colors.get(level, C.TEXT_DIM)
        ic = icons.get(level, ft.Icons.CIRCLE)
        row = ft.Container(
            content=ft.Row([ft.Text(time.strftime("%H:%M:%S"), size=10, color=C.SUBTEXT, font_family="Consolas", width=56),
                            ft.Icon(ic, size=12, color=c),
                            ft.Text(msg, size=10, color=C.TEXT, font_family="Consolas", selectable=True, expand=True, no_wrap=False)],
                           spacing=6, vertical_alignment=ft.CrossAxisAlignment.START),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4), border_radius=6, bgcolor=ft.Colors.with_opacity(0.05, c),
        )
        log_list.controls.append(row)
        file_log(f"[{level}] {msg}")
        try: page.update()
        except Exception: pass

    def set_status(text, color=C.SUBTEXT, dot_color=None):
        status_text.value = text
        status_text.color = color
        status_dot.bgcolor = dot_color or color
        try: page.update()
        except Exception: pass

    def update_status_from_state():
        try:
            sys_on = is_system_proxy_enabled()
            relay_on = relays.is_port_open("127.0.0.1", C.LOCAL_PORT, timeout=0.3)
            proxy_set = bool(current_proxy_from_ui())
            if sys_on and relay_on: set_status("🌐 Системный прокси активен (весь ПК)", C.SUCCESS, C.SUCCESS)
            elif relay_on and proxy_set: set_status("🔒 Локальный прокси активен (Chrome)", C.PURPLE, C.PURPLE)
            elif proxy_set: set_status("Готов к запуску (прокси задан)", C.WARNING, C.WARNING)
            else: set_status("Прямой интернет (прокси не задан)", C.CYAN, C.CYAN)
        except Exception: pass

    speed_down_text = ft.Text("0.0", size=16, color=C.SUCCESS, weight=ft.FontWeight.W_800, font_family="Consolas")
    speed_up_text = ft.Text("0.0", size=16, color=C.PINK, weight=ft.FontWeight.W_800, font_family="Consolas")
    ping_text = ft.Text("—", size=16, color=C.WARNING, weight=ft.FontWeight.W_800, font_family="Consolas")
    monitor_ip_value = ft.Text("—", size=14, color=C.CYAN, font_family="Consolas", weight=ft.FontWeight.W_800)

    async def speed_monitor():
        calc_speed()
        while True:
            try:
                up, down = calc_speed()
                speed_down_text.value = f"{down/1024:.1f}M" if down > 1024 else f"{down:.1f}"
                speed_up_text.value = f"{up/1024:.1f}M" if up > 1024 else f"{up:.1f}"
                page.update()
            except Exception: pass
            await asyncio.sleep(1.0)

    async def ping_monitor():
        while True:
            try:
                loop = asyncio.get_event_loop()
                ping = await loop.run_in_executor(None, measure_ping, 5)
                if ping < 0: ping_text.value, ping_text.color = "—", C.SUBTEXT
                else:
                    ping_text.value = f"{ping:.0f}"
                    ping_text.color = C.SUCCESS if ping < 300 else C.WARNING
                page.update()
            except Exception: pass
            await asyncio.sleep(10.0)

    async def refresh_ip_async():
        ip_text.value = "IP: ..."
        try: page.update()
        except Exception: pass
        loop = asyncio.get_event_loop()
        ip = await loop.run_in_executor(None, get_current_ip)
        ip_text.value = f"IP: {ip}"
        monitor_ip_value.value = ip
        try: page.update()
        except Exception: pass

    async def ip_monitor():
        try: await refresh_ip_async()
        except Exception: pass
        while True:
            await asyncio.sleep(15.0)
            try: await refresh_ip_async()
            except Exception: pass

    url_input = ft.TextField(
        hint_text="Вставь ссылку и нажми Enter...", border_color=C.BORDER, focused_border_color=C.PURPLE, color=C.TEXT,
        hint_style=ft.TextStyle(color=C.SUBTEXT, size=11), bgcolor=C.BG_INPUT, border_radius=10,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=12), expand=True, text_size=12, cursor_color=C.PURPLE,
        on_submit=lambda e: add_url(),
    )
    url_list = ft.ListView(spacing=4, padding=ft.Padding.symmetric(vertical=4), auto_scroll=True, expand=True)
    url_count_text = ft.Text("0", size=11, color=C.PURPLE, weight=ft.FontWeight.W_700, font_family="Consolas")

    def get_urls(): return [c.data for c in url_list.controls]

    def save_and_refresh():
        state_mod.save_urls(get_urls())
        url_count_text.value = str(len(get_urls()))

    tile_factory = {"fn": None}

    def add_url(e=None):
        raw = (url_input.value or "").strip()
        if not raw or not tile_factory["fn"]: return
        parts = [p for p in raw.replace(",", " ").split() if p]
        existing = get_urls()
        for p in parts:
            url = state_mod.normalize_url(p)
            if not url or url in existing: continue
            idx = len(existing) + 1
            url_list.controls.append(tile_factory["fn"](url, idx))
            existing.append(url)
        url_input.value = ""
        save_and_refresh()
        page.update()

    async def paste_and_add(e=None):
        try: text = await page.get_clipboard_async()
        except Exception: return
        text = (text or "").strip()
        if not text or not tile_factory["fn"]: return
        parts = [p for p in text.replace(",", " ").replace("\\n", " ").split() if p]
        existing = get_urls()
        for p in parts:
            url = state_mod.normalize_url(p)
            if not url or url in existing: continue
            idx = len(existing) + 1
            url_list.controls.append(tile_factory["fn"](url, idx))
            existing.append(url)
        save_and_refresh()
        page.update()

    def clear_urls(e=None):
        url_list.controls.clear()
        save_and_refresh()
        page.update()

    randomization_state = {"value": True}
    randomization_switch = ft.Switch(value=True, active_color=C.PURPLE, inactive_thumb_color=C.SUBTEXT, inactive_track_color=C.BORDER,
                                     on_change=lambda e: randomization_state.update({"value": e.control.value}) or page.update())

    mode_switch = ft.Switch(value=(state.get("mode") == "singbox"), active_color=C.CYAN, inactive_thumb_color=C.SUBTEXT, inactive_track_color=C.BORDER)
    def on_mode_toggle(e):
        state["mode"] = "singbox" if e.control.value else "gost"
        state_mod.save_state(state)
        page.update()
    mode_switch.on_change = on_mode_toggle

    webrtc_switch = ft.Switch(value=state.get("webrtc_block", True), active_color=C.SUCCESS)
    def on_webrtc_change(e):
        state["webrtc_block"] = e.control.value
        state_mod.save_state(state)
    webrtc_switch.on_change = on_webrtc_change

    # --- Mobile Emulation TEST ---
    mobile_switch = ft.Switch(value=state.get("mobile_emulation", False), active_color=C.WARNING)
    def on_mobile_change(e):
        state["mobile_emulation"] = e.control.value
        state_mod.save_state(state)
    mobile_switch.on_change = on_mobile_change

    auto_rotate_input = ft.TextField(value=str(state.get("auto_rotate_mins", 0)), width=60, height=40, text_size=11, text_align=ft.TextAlign.CENTER)

    async def on_test_proxy(e):
        proxy = current_proxy_from_ui()
        if not proxy: log("❌ Прокси не задан", "error"); return
        log("🔍 Проверяю прокси напрямую...", "step")
        loop = asyncio.get_event_loop()
        ok, msg = await loop.run_in_executor(None, test_proxy_direct, proxy)
        if ok: log(f"✅ Прокси рабочий! IP: {msg}", "success")
        else: log(f"❌ Прокси мертв: {msg}", "error")

    test_proxy_btn = ft.Container(content=ft.Text("Проверить прокси", size=11, color=C.CYAN), padding=8, border_radius=8, bgcolor=C.BG_INPUT,
                                  on_click=lambda e: asyncio.create_task(on_test_proxy(e)))

    sys_proxy_switch = ft.Switch(value=is_system_proxy_enabled(), active_color=C.SUCCESS, inactive_thumb_color=C.SUBTEXT, inactive_track_color=C.BORDER)

    start_btn = gradient_btn("ОЧИСТИТЬ И ЗАПУСТИТЬ БРАУЗЕР", ft.Icons.ROCKET_LAUNCH, C.GRAD_PURPLE, on_click=lambda e: asyncio.create_task(start_clean()), height=54)
    start_btn_wrapper = ft.Container(content=start_btn, opacity=1.0, animate_opacity=200)
    rotate_btn = gradient_btn("СМЕНИТЬ IP", ft.Icons.CACHED, C.GRAD_PINK, on_click=lambda e: asyncio.create_task(manual_rotate()), height=54)

    def set_busy_state(is_busy):
        busy["value"] = is_busy
        try:
            start_btn.disabled = is_busy
            rotate_btn.disabled = is_busy
            start_btn_wrapper.opacity = 0.5 if is_busy else 1.0
            page.update()
        except Exception: pass

    async def start_clean():
        if busy["value"]: return
        set_busy_state(True)
        log_list.controls.clear()
        loop = asyncio.get_event_loop()
        try:
            log("══════════════════════════", "step")
            log("🚀 ЗАПУСК", "step")
            log("══════════════════════════", "step")

            browser = browser_state["value"]
            b_cfg = C.BROWSERS[browser]
            b_title = b_cfg["title"]
            exe = find_browser_exe(browser)
            if not exe:
                log(f"❌ {b_title} не найден", "error")
                set_status(f"Ошибка: {b_title} не найден", C.DANGER, C.DANGER)
                return
            log(f"✅ {b_title}: {os.path.basename(exe)}", "success")

            data = get_user_data_path(browser)
            if not os.path.exists(data):
                log("❌ Профиль не найден", "error")
                set_status("Ошибка", C.DANGER, C.DANGER)
                return
            temp_profile = get_browser_temp_profile(browser)

            proxy = current_proxy_from_ui()
            urls = get_urls()
            if not urls:
                log("⚠️ Список сайтов пуст", "warn")
                set_status("Ошибка: список пуст", C.DANGER, C.DANGER)
                return
            log(f"✅ Ссылок: {len(urls)}", "success")

            if not proxy:
                log("ℹ️ Прокси не задан — обычный интернет", "info")
                set_status("Прямой интернет", C.CYAN, C.CYAN)
                await loop.run_in_executor(None, clear_system_proxy)
                await loop.run_in_executor(None, relays.stop_relays)
                await loop.run_in_executor(None, kill_all_browser, browser, log)
                await loop.run_in_executor(None, prepare_temp_profile, browser, log)
                await loop.run_in_executor(None, full_clean, data, log, None)
                chrome_args = [f"--user-data-dir={temp_profile}", "--no-first-run", "--no-default-browser-check", "--disable-session-crashed-bubble", "--disable-features=InfiniteSessionRestore", "--disable-extensions", "--disable-plugins", "--no-service-autorun", "--password-store=basic"]
                if randomization_state["value"]: random.shuffle(urls)
                for i, url in enumerate(urls, 1):
                    cmd = ([exe] + chrome_args + (["--new-window", url] if i == 1 else [url]))
                    try:
                        relays._popen_hidden(cmd)
                        log(f"✅ [{i}/{len(urls)}] {url}", "success")
                        await asyncio.sleep(random.uniform(2.5, 6.0) if randomization_state["value"] else 0.6)
                    except Exception as e: log(f"❌ {url}: {str(e)[:80]}", "error")
                log("🎉 ГОТОВО! (прямой интернет)", "success")
                set_status("Готово (прямой интернет)", C.SUCCESS, C.SUCCESS)
                await refresh_ip_async()
                return

            log(f"✅ Прокси: {proxy['scheme']}://{proxy['host']}:{proxy['port']}", "success")
            use_singbox = (state.get("mode") == "singbox")
            log(f"🔀 Режим: {'sing-box' if use_singbox else 'gost'}", "info")

            hooks.run("before_relay_start", proxy, log)

            if use_singbox:
                if not os.path.exists(C.SINGBOX_EXE): await loop.run_in_executor(None, relays.install_singbox, log)
                ok = await loop.run_in_executor(None, relays.start_singbox, proxy, log)
            else:
                if not os.path.exists(C.GOST_EXE): await loop.run_in_executor(None, relays.install_gost, log)
                ok = await loop.run_in_executor(None, relays.start_gost, proxy, log)
            if not ok:
                log("❌ Релей не запустился", "error")
                set_status("Ошибка", C.DANGER, C.DANGER)
                return

            hooks.run("after_relay_ready", proxy, log)
            update_status_from_state()

            await asyncio.sleep(2)
            log("🔍 Проверяю соединение...", "step")
            result, ok = None, False
            for attempt in range(3):
                try:
                    ok, result = await asyncio.wait_for(loop.run_in_executor(None, relays.check_relay, 12), timeout=17.0)
                except asyncio.TimeoutError:
                    ok, result = False, "timeout"
                if ok: break
                log(f"⏱ Попытка {attempt + 1}/3: {result}", "warn")
                await asyncio.sleep(2)
            if not ok:
                log("❌ Прокси не отвечает", "error")
                set_status("Ошибка", C.DANGER, C.DANGER)
                return
            log(f"✅ IP: {result}", "success")
            set_status(f"Локальный прокси активен | IP: {result}", C.SUCCESS, C.SUCCESS)
            ip_text.value = f"IP: {result}"

            log("🧹 ОЧИСТКА БРАУЗЕРА", "step")
            await loop.run_in_executor(None, kill_all_browser, browser, log)
            await loop.run_in_executor(None, prepare_temp_profile, browser, log)
            await loop.run_in_executor(None, full_clean, data, log, None)
            hooks.run("after_clean", 0, 0, log)

            log("🌐 ОТКРЫТИЕ САЙТОВ", "step")
            proxy_arg = f"--proxy-server={proxy['scheme']}://127.0.0.1:{C.LOCAL_PORT}"
            chrome_args = [
                f"--user-data-dir={temp_profile}", proxy_arg, "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1",
                "--no-first-run", "--no-default-browser-check", "--disable-session-crashed-bubble",
                "--disable-features=InfiniteSessionRestore", "--disable-dns-prefetch", "--disable-background-networking",
                "--disable-component-update", "--disable-sync", "--disable-extensions", "--disable-plugins",
                "--no-service-autorun", "--password-store=basic", "--disable-gpu-shader-disk-cache",
            ]
            if state.get("webrtc_block", True): chrome_args.append("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
            
            if state.get("mobile_emulation", False):
                devices = [
                    ("Samsung Galaxy S23", "SM-S911B"), ("Samsung Galaxy S22", "SM-S901B"),
                    ("Google Pixel 7", "Pixel 7"), ("Google Pixel 6", "Pixel 6"),
                    ("Xiaomi 13 Pro", "2210132G"), ("Xiaomi Redmi Note 12", "22111317G"),
                    ("OnePlus 11", "CPH2449"), ("OnePlus 10 Pro", "NE2213"),
                    ("Sony Xperia 1 IV", "XQ-CT54"), ("Asus ROG Phone 6", "AI2201"),
                ]
                android_versions = ["11", "12", "13", "14"]
                chrome_versions = ["114.0.5735.196", "115.0.5790.166", "116.0.5845.163", "117.0.5938.60", "118.0.5993.80"]
                
                dev_name, dev_model = random.choice(devices)
                os_ver = random.choice(android_versions)
                chrome_ver = random.choice(chrome_versions)
                
                ua = f"Mozilla/5.0 (Linux; Android {os_ver}; {dev_model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36"
                
                log(f"📱 Мобильный отпечаток: {dev_name} (Android {os_ver}, Chrome {chrome_ver.split('.')[0]})", "info")
                
                chrome_args.append(f"--user-agent={ua}")
                chrome_args.append("--touch-events=enabled")
                chrome_args.append("--enable-mobile-emulation")
                chrome_args.append("--window-size=390,844")
            
            hooks.run("before_chrome_launch", chrome_args, urls, log)
            if randomization_state["value"]: random.shuffle(urls)
            for i, url in enumerate(urls, 1):
                cmd = ([exe] + chrome_args + (["--new-window", url] if i == 1 else [url]))
                try:
                    relays._popen_hidden(cmd)
                    log(f"✅ [{i}/{len(urls)}] {url}", "success")
                    await asyncio.sleep(random.uniform(2.5, 6.0) if randomization_state["value"] else 0.6)
                except Exception as e: log(f"❌ {url}: {str(e)[:80]}", "error")
            log("🎉 ГОТОВО!", "success")
            set_status(f"Локальный прокси | IP: {result}", C.SUCCESS, C.SUCCESS)
        except Exception as ex:
            log(f"❌ Ошибка: {ex}", "error")
            log(traceback.format_exc(), "error")
            set_status("Ошибка", C.DANGER, C.DANGER)
        finally:
            set_busy_state(False)

    async def auto_rotate_monitor():
        while True:
            await asyncio.sleep(60)
            mins = int(state.get("auto_rotate_mins", 0))
            if mins > 0 and not busy["value"]:
                elapsed = time.time() - last_rotation_ts["value"]
                if elapsed > mins * 60: await manual_rotate()

    async def manual_rotate():
        if busy["value"]: return
        now = time.time()
        elapsed = now - last_rotation_ts["value"]
        if last_rotation_ts["value"] > 0 and elapsed < C.ROTATION_COOLDOWN: return
        busy["value"] = True
        log("🔄 РОТАЦИЯ IP", "step")
        try:
            loop = asyncio.get_event_loop()
            rot_url = rotation_url_input.value.strip()
            if pool_state["list"]:
                ok, new_proxy, next_idx = trigger_pool_rotation(pool_state["list"], pool_state["idx"], log)
                if ok:
                    pool_state["idx"] = next_idx
                    parts = new_proxy.split(":")
                    proxy_host_input.value = parts[0]
                    proxy_port_input.value = parts[1] if len(parts) > 1 else ""
                    proxy_user_input.value = ""
                    proxy_pass_input.value = ""
                    save_fields()
                    log(f"✅ Новый прокси: {proxy_host_input.value}:{proxy_port_input.value}", "success")
                    await loop.run_in_executor(None, relays.stop_relays)
                    await loop.run_in_executor(None, relays.start_singbox, current_proxy_from_ui(), log)
                    await refresh_ip_async()
                    return
            elif not rot_url:
                return
            sys_proxy_was_on = is_system_proxy_enabled()
            if sys_proxy_was_on:
                await loop.run_in_executor(None, clear_system_proxy, None)
                await asyncio.sleep(2)
            try:
                try:
                    ok, msg, code = await asyncio.wait_for(loop.run_in_executor(None, trigger_rotation, rot_url, log), timeout=60.0)
                except asyncio.TimeoutError:
                    return
                hooks.run("on_rotation", ok, msg, log)
                if not ok: return
                last_rotation_ts["value"] = time.time()
                if code == 429: await asyncio.sleep(20)
                else: await asyncio.sleep(12)
            finally:
                if sys_proxy_was_on:
                    await loop.run_in_executor(None, set_system_proxy, "127.0.0.1", C.LOCAL_PORT, None)
                    await asyncio.sleep(1)
            await refresh_ip_async()
        except Exception: pass
        finally:
            busy["value"] = False
            page.update()

    async def on_system_proxy_toggle(e):
        enable = e.control.value
        loop = asyncio.get_event_loop()
        if enable:
            proxy = current_proxy_from_ui()
            if not proxy:
                e.control.value = False
                page.update()
                return
            use_singbox = (state.get("mode") == "singbox")
            if use_singbox:
                if not os.path.exists(C.SINGBOX_EXE): await loop.run_in_executor(None, relays.install_singbox, log)
                ok = await loop.run_in_executor(None, relays.start_singbox, proxy, log)
            else:
                if not os.path.exists(C.GOST_EXE): await loop.run_in_executor(None, relays.install_gost, log)
                ok = await loop.run_in_executor(None, relays.start_gost, proxy, log)
            if not ok:
                e.control.value = False
                page.update()
                return
            sys_ok = await loop.run_in_executor(None, set_system_proxy, "127.0.0.1", C.LOCAL_PORT, log)
            if not sys_ok:
                e.control.value = False
                page.update()
                return
            await refresh_ip_async()
        else:
            await loop.run_in_executor(None, clear_system_proxy, log)
            await loop.run_in_executor(None, relays.stop_relays, log)
            update_status_from_state()
        page.update()

    sys_proxy_switch.on_change = on_system_proxy_toggle

    ctx = {
        "page": page, "browser_dropdown": browser_dropdown, "browser_kill_btn": browser_kill_btn,
        "proxy_host_input": proxy_host_input, "proxy_port_input": proxy_port_input,
        "proxy_user_input": proxy_user_input, "proxy_pass_input": proxy_pass_input,
        "proxy_type_input": proxy_type_input, "rotation_url_input": rotation_url_input,
        "rotate_btn": rotate_btn, "sys_proxy_switch": sys_proxy_switch, "mode_switch": mode_switch,
        "randomization_switch": randomization_switch, "url_input": url_input, "url_list": url_list,
        "url_count_text": url_count_text, "save_and_refresh": save_and_refresh,
        "paste_and_add": paste_and_add, "clear_urls": clear_urls, "log_list": log_list,
        "speed_down_text": speed_down_text, "speed_up_text": speed_up_text,
        "ping_text": ping_text, "monitor_ip_value": monitor_ip_value, "refresh_ip_async": refresh_ip_async,
        "webrtc_switch": webrtc_switch, "auto_rotate_input": auto_rotate_input, "test_proxy_btn": test_proxy_btn,
        "mobile_switch": mobile_switch,
    }
    tabs = build_tabs(ctx)
    
    # --- DEV TOOLS TAB ---
    if C.DEV_MODE:
        dev_tab = ft.Column([
            ft.Text("Панель разработчика", size=16, weight=ft.FontWeight.W_700, color=C.PURPLE),
            ft.Text("Управление релизами и патчами", size=11, color=C.SUBTEXT),
            ft.Container(height=10),
            ft.TextField(label="GitHub Token", value=GITHUB_TOKEN, password=True, can_reveal_password=True, text_size=12),
            ft.Container(height=10),
            ft.TextField(label="Версия для релиза", value="1.4.2", text_size=12),
            ft.Container(height=10),
            ft.ElevatedButton("Собрать EXE", icon=ft.Icons.BUILD, on_click=lambda e: asyncio.create_task(do_build())),
            ft.ElevatedButton("Выпустить релиз на GitHub", icon=ft.Icons.UPLOAD, on_click=lambda e: asyncio.create_task(do_publish())),
            ft.Container(height=20),
            ft.Text("Загрузка патча (.patch)", size=14, color=C.WARNING),
            ft.TextField(label="Путь к файлу .patch", text_size=12),
            ft.ElevatedButton("Применить патч", icon=ft.Icons.FILE_DOWNLOAD, on_click=lambda e: asyncio.create_task(do_patch()))
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        
        tabs["pages"].append(dev_tab)
        tabs["labels"].append(("DevTools", ft.Icons.DEVELOPER_MODE))
    
    tile_factory["fn"] = ctx["create_url_tile"]

    tab_buttons = []
    tabs_container = tabs["tabs_container"]

    def _switch(idx, btns):
        switch_tab(idx, btns, tabs_container, tabs["pages"], page)

    for i, (label, icon) in enumerate(tabs["labels"]):
        tab_buttons.append(make_tab_btn(label, icon, i, _switch, tab_buttons))

    tabs_row = ft.Container(content=ft.Row(tab_buttons, spacing=4), padding=ft.Padding.symmetric(horizontal=14, vertical=8))

    update_info = {"version": None, "url": None}
    
    async def check_updates_on_start():
        latest, url = await asyncio.get_event_loop().run_in_executor(None, check_for_updates)
        if latest:
            update_info["version"] = latest
            update_info["url"] = url
            log(f"🚀 Доступно обновление: v{latest} (текущая: v{C.CURRENT_VERSION})", "warn")
            update_btn.content.value = f"Обновить до v{latest}"
            update_btn.visible = True
            page.update()

    async def do_update(e):
        if not update_info["url"]: return
        log("⏳ Скачивание и установка обновления...", "step")
        ok = await asyncio.get_event_loop().run_in_executor(None, download_and_update, update_info["url"])
        if not ok: log("❌ Ошибка обновления (возможно, вы запустили не EXE)", "error")

    update_btn = ft.Container(
        content=ft.Text("Обновить", size=11, color="white", weight=ft.FontWeight.W_700),
        padding=ft.Padding.symmetric(vertical=8, horizontal=16), bgcolor=C.SUCCESS, border_radius=8,
        on_click=lambda e: asyncio.create_task(do_update(e)), visible=False,
    )
    
    page.run_task(check_updates_on_start)

    content = ft.Column([
        build_title_bar(page),
        tabs_row,
        ft.Container(content=tabs_container, padding=ft.Padding.symmetric(horizontal=14, vertical=4), expand=True),
        build_action_bar(start_btn_wrapper),
        ft.Container(content=ft.Row([build_status_bar(status_dot, status_text, ip_text), update_btn]), padding=ft.Padding.symmetric(horizontal=14, vertical=4), bgcolor=C.BG_TITLEBAR),
    ], spacing=0, expand=True)

    page.add(ft.Container(content=content, gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT, colors=[C.BG, C.BG_DEEP]), expand=True))

    for idx, u in enumerate(state_mod.load_urls(), 1):
        url_list.controls.append(tile_factory["fn"](u, idx))
    url_count_text.value = str(len(url_list.controls))

    switch_tab(0, tab_buttons, tabs_container, tabs["pages"], page)

    page.run_task(speed_monitor)
    page.run_task(ping_monitor)
    page.run_task(ip_monitor)
    page.run_task(auto_rotate_monitor)

    update_status_from_state()

    log("👋 Proxy Combo готов", "info")
    try:
        from version import VERSION
        log(f"🏷  Версия {VERSION}", "info")
    except Exception: pass
    log("💡 Прокси не задан? Chrome откроется через обычный интернет", "info")
'''
    write_file("proxycombo/app.py", app_code)

    print("✅ DevTools успешно установлены!")
    print("💡 Теперь запусти: python main.py --debug")
    print("💡 В приложении появится новая вкладка 'DevTools'.")

if __name__ == "__main__":
    main()