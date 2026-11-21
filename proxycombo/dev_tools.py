import os
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
