import os

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
    print("🔧 Устанавливаю систему обновлений EXE (v1.3.0)...")

    # 1. Бамп версии
    replace_in_file("version.py", 'VERSION = "1.2.0"', 'VERSION = "1.3.0"')
    replace_in_file("proxycombo/config.py", 'CURRENT_VERSION = "1.2.0"', 'CURRENT_VERSION = "1.3.0"')

    # 2. Полная перезапись updater.py
    updater_code = '''
import os
import sys
import json
import urllib.request
import tempfile
import subprocess
import time
from .config import GITHUB_REPO, GITHUB_TOKEN, CURRENT_VERSION
from .logging_utils import file_log, dbg

def check_for_updates():
    """Возвращает (version, download_url) если есть обновление, иначе (None, None)."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        headers = {"User-Agent": "ProxyCombo"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
            
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            latest = data.get("tag_name", "").lstrip("v")
            
            if latest and latest != CURRENT_VERSION:
                # Ищем прикрепленный exe-файл
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".exe"):
                        return latest, asset["browser_download_url"]
    except Exception as e:
        dbg(f"Update check failed: {e}")
    return None, None

def download_and_update(download_url):
    """Скачивает новый exe и запускает батник для подмены файла."""
    try:
        # Если мы запущены не как exe, обновление exe не сработает
        if not getattr(sys, "frozen", False):
            file_log("Запущено из исходников. Пропускаю авто-обновление exe.")
            return False

        current_exe = sys.executable
        temp_dir = tempfile.gettempdir()
        new_exe_path = os.path.join(temp_dir, "ProxyCombo_new.exe")
        
        file_log(f"Скачивание обновления: {download_url}")
        
        headers = {"User-Agent": "ProxyCombo"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        # Скачиваем новый exe
        req = urllib.request.Request(download_url, headers=headers)
        with urllib.request.urlopen(req) as r, open(new_exe_path, 'wb') as f:
            f.write(r.read())
            
        # Создаем батник для подмены
        bat_path = os.path.join(temp_dir, "update_proxycombo.bat")
        with open(bat_path, "w", encoding="cp866") as f:
            f.write("@echo off\\n")
            f.write("timeout /t 2 /nobreak > NUL\\n") # Ждем закрытия текущего exe
            f.write(f'copy /y "{new_exe_path}" "{current_exe}"\\n')
            f.write(f'start "" "{current_exe}"\\n')
            f.write(f'del "{new_exe_path}"\\n')
            f.write("del %~f0\\n") # Удаляем сам батник
            
        # Запускаем батник скрытно и закрываем текущее приложение
        subprocess.Popen([bat_path], shell=True, creationflags=0x08000000)
        time.sleep(0.5)
        sys.exit(0)
        
    except Exception as e:
        file_log(f"Ошибка обновления: {e}")
        return False
'''
    write_file("proxycombo/updater.py", updater_code)

    # 3. Изменения в app.py
    # Импорт новых функций
    replace_in_file("proxycombo/app.py", 
        'from .updater import check_for_updates, apply_update',
        'from .updater import check_for_updates, download_and_update')

    # Удаляем старую проверку и добавляем UI-элементы
    app_ui_old = '''    async def check_updates_on_start():
        latest, assets = await asyncio.get_event_loop().run_in_executor(None, check_for_updates)
        if latest:
            log(f"🚀 Доступно обновление: v{latest} (текущая: v{C.CURRENT_VERSION})", "warn")
            log("💡 Скачайте новый патч с GitHub и примените его.", "info")
    
    page.run_task(check_updates_on_start)'''
    
    app_ui_new = '''    update_info = {"version": None, "url": None}

    async def check_updates_on_start():
        latest, url = await asyncio.get_event_loop().run_in_executor(None, check_for_updates)
        if latest:
            update_info["version"] = latest
            update_info["url"] = url
            log(f"🚀 Доступно обновление: v{latest} (текущая: v{C.CURRENT_VERSION})", "warn")
            update_btn.visible = True
            page.update()

    async def do_update(e):
        if not update_info["url"]:
            return
        log("⏳ Скачивание и установка обновления...", "step")
        ok = await asyncio.get_event_loop().run_in_executor(
            None, download_and_update, update_info["url"]
        )
        if not ok:
            log("❌ Ошибка обновления (возможно, вы запустили не EXE)", "error")

    update_btn = ft.Container(
        content=ft.Text("Обновить до v" + str(update_info["version"]) if update_info["version"] else "Обновить", 
                        size=11, color="white", weight=ft.FontWeight.W_700),
        padding=ft.Padding.symmetric(vertical=8, horizontal=16),
        bgcolor=C.SUCCESS, border_radius=8,
        on_click=lambda e: asyncio.create_task(do_update(e)),
        visible=False,
    )
    
    page.run_task(check_updates_on_start)'''
    
    replace_in_file("proxycombo/app.py", app_ui_old, app_ui_new)

    # Добавляем кнопку в status bar
    replace_in_file("proxycombo/app.py", 
        'build_status_bar(status_dot, status_text, ip_text),',
        'ft.Container(content=build_status_bar(status_dot, status_text, ip_text), padding=ft.Padding.only(bottom=10)),\n            update_btn,')

    # Добавляем отступы для кнопки в layout
    app_layout_old = '''            build_action_bar(start_btn_wrapper),
            build_status_bar(status_dot, status_text, ip_text),
        ],'''
    app_layout_new = '''            build_action_bar(start_btn_wrapper),
            ft.Container(
                content=ft.Row([build_status_bar(status_dot, status_text, ip_text), update_btn]),
                padding=ft.Padding.symmetric(horizontal=14, vertical=4),
                bgcolor=C.BG_TITLEBAR,
            ),
        ],'''
    replace_in_file("proxycombo/app.py", app_layout_old, app_layout_new)

    print("✅ Система обновлений EXE готова! (Версия 1.3.0)")
    print("💡 Запусти python main.py --debug")

if __name__ == "__main__":
    main()