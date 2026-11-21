import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def replace_in_file(rel_path, old, new):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        print(f"❌ Файл не найден: {rel_path}")
        return False
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if old not in content:
        print(f"⚠️  Строка не найдена в {rel_path}. Возможно, патч уже применён.")
        return False
    
    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return True

def main():
    print("🔧 Применяю патч 1.1.0 (Добавление Yandex Browser)...")

    # 1. version.py
    replace_in_file("version.py", 'VERSION = "1.0.0"', 'VERSION = "1.1.0"')

    # 2. config.py
    cfg_add = '''
# ---- Браузеры ----
BROWSERS = {
    "chrome": {
        "title": "Google Chrome",
        "exe": "chrome.exe",
        "processes": ["chrome.exe"],
        "paths": [
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            r"%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe",
        ],
        "user_data": r"%LOCALAPPDATA%\\Google\\Chrome\\User Data",
        "registry": r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe",
    },
    "yandex": {
        "title": "Yandex Browser",
        "exe": "browser.exe",
        "processes": ["browser.exe", "yandex_browser.exe"],
        "paths": [
            r"C:\\Program Files\\Yandex\\YandexBrowser\\Application\\browser.exe",
            r"C:\\Program Files (x86)\\Yandex\\YandexBrowser\\Application\\browser.exe",
            r"%LOCALAPPDATA%\\Yandex\\YandexBrowser\\Application\\browser.exe",
        ],
        "user_data": r"%LOCALAPPDATA%\\Yandex\\YandexBrowser\\User Data",
        "registry": r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\browser.exe",
    },
}

DEFAULT_BROWSER = "chrome"
TEMP_PROFILE_YANDEX = os.path.join(
    os.environ.get("TEMP", tempfile.gettempdir()),
    "yandex_cleaner_profile",
)

'''
    replace_in_file("proxycombo/config.py", 'BG_DEEP = "#1a1a22"', cfg_add + 'BG_DEEP = "#1a1a22"')

    # 3. state.py
    replace_in_file("proxycombo/state.py", '"mode": "singbox",', '"mode": "singbox",\n        "browser": "chrome",')

    # 4. relays.py
    relays_add = '''
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
'''
    replace_in_file("proxycombo/relays.py", 'def get_chrome_processes():', relays_add)

    # 5. chrome.py - перезаписываем полностью
    chrome_code = '''import os
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
'''
    with open(os.path.join(ROOT, "proxycombo/chrome.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(chrome_code)

    # 6. ui/tabs.py
    tabs_old = '''                        ft.Text("Оставь пустым — Chrome откроется через обычный интернет",
                                size=10, color=C.SUBTEXT),
                        ft.Container(height=12),
                        ft.Row([ctx["proxy_host_input"], ctx["proxy_port_input"]],'''
    tabs_new = '''                        ft.Text("Оставь пустым — браузер откроется через обычный интернет",
                                size=10, color=C.SUBTEXT),
                        ft.Container(height=10),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.WEB, size=14, color=C.ORANGE),
                                ft.Text("Браузер", size=11, color=C.TEXT,
                                        weight=ft.FontWeight.W_600),
                                ft.Container(expand=True),
                                ctx["browser_dropdown"],
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=6),
                        ctx["browser_kill_btn"],
                        ft.Container(height=12),
                        ft.Row([ctx["proxy_host_input"], ctx["proxy_port_input"]],'''
    replace_in_file("proxycombo/ui/tabs.py", tabs_old, tabs_new)

    # 7. app.py
    app_imports_old = '''from .chrome import (find_chrome_exe, get_user_data_path, kill_all_chrome,
                     full_clean, prepare_temp_profile)'''
    app_imports_new = '''from .chrome import (find_browser_exe, get_user_data_path, kill_all_browser,
                     kill_all_chrome, full_clean, prepare_temp_profile,
                     get_browser_temp_profile)'''
    replace_in_file("proxycombo/app.py", app_imports_old, app_imports_new)

    app_ui_old = '''    rotation_url_input.value = state.get("rotation_url", "")

    def current_proxy_from_ui():'''
    app_ui_new = '''    rotation_url_input.value = state.get("rotation_url", "")

    # ------- Браузер -------
    browser_state = {"value": state.get("browser", C.DEFAULT_BROWSER)}
    if browser_state["value"] not in C.BROWSERS:
        browser_state["value"] = C.DEFAULT_BROWSER

    browser_dropdown = ft.Dropdown(
        label="Браузер",
        value=browser_state["value"],
        options=[
            ft.dropdown.Option(k, v["title"])
            for k, v in C.BROWSERS.items()
        ],
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
        ok = await asyncio.get_event_loop().run_in_executor(
            None, kill_all_browser, b, log
        )
        if ok:
            log(f"✅ {title} закрыт", "success")

    browser_kill_btn = ft.Container(
        content=ft.Row(
            [ft.Icon(ft.Icons.CLOSE, size=14, color=C.DANGER),
             ft.Text("Закрыть браузер", size=11, color=C.TEXT)],
            spacing=6, alignment=ft.MainAxisAlignment.CENTER,
        ),
        on_click=on_kill_browser,
        padding=ft.Padding.symmetric(vertical=8, horizontal=12),
        bgcolor=C.BG_INPUT,
        border=ft.Border.all(1, C.BORDER_SOFT),
        border_radius=10,
    )

    def current_proxy_from_ui():'''
    replace_in_file("proxycombo/app.py", app_ui_old, app_ui_new)

    app_logic_old = '''            log("══════════════════════════", "step")
            log("🚀 ЗАПУСК", "step")
            log("══════════════════════════", "step")

            exe = find_chrome_exe()
            if not exe:
                log("❌ Chrome не найден", "error")
                set_status("Ошибка: Chrome не найден", C.DANGER, C.DANGER)
                return
            log(f"✅ Chrome: {os.path.basename(exe)}", "success")

            data = get_user_data_path()
            if not os.path.exists(data):
                log("❌ Профиль не найден", "error")
                set_status("Ошибка", C.DANGER, C.DANGER)
                return'''
    app_logic_new = '''            log("══════════════════════════", "step")
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
            temp_profile = get_browser_temp_profile(browser)'''
    replace_in_file("proxycombo/app.py", app_logic_old, app_logic_new)

    replace_in_file("proxycombo/app.py", 
        'await loop.run_in_executor(None, kill_all_chrome, log)\n                await loop.run_in_executor(None, prepare_temp_profile, log)',
        'await loop.run_in_executor(None, kill_all_browser, browser, log)\n                await loop.run_in_executor(None, prepare_temp_profile, browser, log)')
    
    replace_in_file("proxycombo/app.py",
        'f"--user-data-dir={C.TEMP_PROFILE}",',
        'f"--user-data-dir={temp_profile}",')

    app_ctx_old = '''    ctx = {
        "page": page,
        "proxy_host_input": proxy_host_input'''
    app_ctx_new = '''    ctx = {
        "page": page,
        "browser_dropdown": browser_dropdown,
        "browser_kill_btn": browser_kill_btn,
        "proxy_host_input": proxy_host_input'''
    replace_in_file("proxycombo/app.py", app_ctx_old, app_ctx_new)

    print("✅ Патч успешно применён! (Версия 1.1.0)")
    print("💡 Проверь: python main.py --debug")

if __name__ == "__main__":
    main()