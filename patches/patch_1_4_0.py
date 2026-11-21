import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write_file(rel_path, content):
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f: 
        f.write(content)

def main():
    print("🔧 Кардинальное исправление app.py и updater.py (v1.4.0)...")

    # 1. Обновляем версии
    v_path = os.path.join(ROOT, "version.py")
    with open(v_path, "r", encoding="utf-8") as f: v_content = f.read()
    v_content = re.sub(r'VERSION = ".*?"', 'VERSION = "1.4.0"', v_content)
    with open(v_path, "w", encoding="utf-8", newline="\n") as f: f.write(v_content)

    c_path = os.path.join(ROOT, "proxycombo/config.py")
    with open(c_path, "r", encoding="utf-8") as f: c_content = f.read()
    c_content = re.sub(r'CURRENT_VERSION = ".*?"', 'CURRENT_VERSION = "1.4.0"', c_content)
    with open(c_path, "w", encoding="utf-8", newline="\n") as f: f.write(c_content)

    # 2. Полная перезапись updater.py
    updater_code = '''import os
import sys
import json
import urllib.request
import tempfile
import subprocess
import time
from .config import GITHUB_REPO, GITHUB_TOKEN, CURRENT_VERSION
from .logging_utils import file_log, dbg

def check_for_updates():
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
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".exe"):
                        return latest, asset["browser_download_url"]
    except Exception as e:
        dbg(f"Update check failed: {e}")
    return None, None

def download_and_update(download_url):
    try:
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
        
        req = urllib.request.Request(download_url, headers=headers)
        with urllib.request.urlopen(req) as r, open(new_exe_path, 'wb') as f:
            f.write(r.read())
            
        bat_path = os.path.join(temp_dir, "update_proxycombo.bat")
        with open(bat_path, "w", encoding="cp866") as f:
            f.write("@echo off\\n")
            f.write("timeout /t 2 /nobreak > NUL\\n")
            f.write(f'copy /y "{new_exe_path}" "{current_exe}"\\n')
            f.write(f'start "" "{current_exe}"\\n')
            f.write(f'del "{new_exe_path}"\\n')
            f.write("del %~f0\\n")
            
        subprocess.Popen([bat_path], shell=True, creationflags=0x08000000)
        time.sleep(0.5)
        sys.exit(0)
        
    except Exception as e:
        file_log(f"Ошибка обновления: {e}")
        return False
'''
    write_file("proxycombo/updater.py", updater_code)

    # 3. Полная перезапись app.py
    # Мы берем твой текущий app.py и программно вычищаем оттуда все старые ошибки
    app_path = os.path.join(ROOT, "proxycombo/app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    # Удаляем любые старые следы update_btn и update_info
    app_code = re.sub(r"[ \t]*update_info = \{.*?\n", "", app_code)
    app_code = re.sub(r"[ \t]*update_btn = ft\.Container\(.*?\n    \)\n", "", app_code, flags=re.DOTALL)
    app_code = re.sub(r"[ \t]*update_btn_ref = ft\.Ref.*?\n", "", app_code)
    app_code = re.sub(r"[ \t]*async def check_updates_on_start\(\):.*?(?=def |async def |page\.run_task|\Z)", "", app_code, flags=re.DOTALL)
    app_code = re.sub(r"[ \t]*async def do_update\(e\):.*?(?=def |async def |page\.run_task|\Z)", "", app_code, flags=re.DOTALL)
    app_code = re.sub(r"[ \t]*page\.run_task\(check_updates_on_start\)\n", "", app_code)
    
    # Чистим layout от старых кнопок
    app_code = app_code.replace("update_btn_ref.current if update_btn_ref.current else ft.Container()", "ft.Container()")
    app_code = app_code.replace(", update_btn]", ", ft.Container()]")
    
    # Вставляем правильный инициализационный блок ПЕРЕД page.add
    clean_init = '''    update_info = {"version": None, "url": None}
    
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
        if not update_info["url"]:
            return
        log("⏳ Скачивание и установка обновления...", "step")
        ok = await asyncio.get_event_loop().run_in_executor(
            None, download_and_update, update_info["url"]
        )
        if not ok:
            log("❌ Ошибка обновления (возможно, вы запустили не EXE)", "error")

    update_btn = ft.Container(
        content=ft.Text("Обновить", size=11, color="white", weight=ft.FontWeight.W_700),
        padding=ft.Padding.symmetric(vertical=8, horizontal=16),
        bgcolor=C.SUCCESS, border_radius=8,
        on_click=lambda e: asyncio.create_task(do_update(e)),
        visible=False,
    )
    
    page.run_task(check_updates_on_start)
'''
    # Ищем место, куда безопасно вставить код (перед page.add)
    app_code = app_code.replace("    page.add(", clean_init + "\n    page.add(", 1)

    # Вставляем update_btn в layout заново
    layout_old = '''            ft.Container(
                content=ft.Row([build_status_bar(status_dot, status_text, ip_text), ft.Container()]),
                padding=ft.Padding.symmetric(horizontal=14, vertical=4),
                bgcolor=C.BG_TITLEBAR,
            ),'''
    
    layout_new = '''            ft.Container(
                content=ft.Row([build_status_bar(status_dot, status_text, ip_text), update_btn]),
                padding=ft.Padding.symmetric(horizontal=14, vertical=4),
                bgcolor=C.BG_TITLEBAR,
            ),'''
    app_code = app_code.replace(layout_old, layout_new)
    
    write_file("proxycombo/app.py", app_code)

    print("✅ Всё исправлено! Версия 1.4.0")
    print("💡 Запусти: python main.py --debug")

if __name__ == "__main__":
    main()