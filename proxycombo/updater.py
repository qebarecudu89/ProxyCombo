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
            f.write("@echo off\n")
            f.write("timeout /t 2 /nobreak > NUL\n")
            f.write(f'copy /y "{new_exe_path}" "{current_exe}"\n')
            f.write(f'start "" "{current_exe}"\n')
            f.write(f'del "{new_exe_path}"\n')
            f.write("del %~f0\n")
            
        subprocess.Popen([bat_path], shell=True, creationflags=0x08000000)
        time.sleep(0.5)
        sys.exit(0)
        
    except Exception as e:
        file_log(f"Ошибка обновления: {e}")
        return False
