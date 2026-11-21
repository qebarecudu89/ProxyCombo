import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def write_file(rel_path, content):
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f: 
        f.write(content)

def main():
    print("🔧 Починка DevTools и добавление выбора файлов (v1.4.2)...")

    # 1. Бамп версий
    v_path = os.path.join(ROOT, "version.py")
    with open(v_path, "r", encoding="utf-8") as f: v_content = f.read()
    v_content = re.sub(r'VERSION = ".*?"', 'VERSION = "1.4.2"', v_content)
    with open(v_path, "w", encoding="utf-8", newline="\n") as f: f.write(v_content)

    c_path = os.path.join(ROOT, "proxycombo", "config.py")
    with open(c_path, "r", encoding="utf-8") as f: c_content = f.read()
    c_content = re.sub(r'CURRENT_VERSION = ".*?"', 'CURRENT_VERSION = "1.4.2"', c_content)
    with open(c_path, "w", encoding="utf-8", newline="\n") as f: f.write(c_content)

    # 2. Перезапись app.py
    app_path = os.path.join(ROOT, "proxycombo", "app.py")
    
    # Мы берем текущий app.py и внедряем в него недостающие функции и FilePicker
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    # Импорт GITHUB_TOKEN
    if "from .config import GITHUB_TOKEN" not in app_code:
        app_code = app_code.replace("from . import config as C", "from . import config as C\nfrom .config import GITHUB_TOKEN")

    # Добавляем FilePicker в начало функции main
    if "file_picker = ft.FilePicker" not in app_code:
        app_code = app_code.replace(
            "async def main(page: ft.Page):",
            "async def main(page: ft.Page):\n    file_picker = ft.FilePicker(on_result=lambda e: asyncio.create_task(on_file_picked(e)))"
        )
        app_code = app_code.replace(
            "page.add(",
            "page.overlay.append(file_picker)\n    page.add("
        )

    # Определяем функции для DevTools перед их использованием
    dev_funcs = '''
    async def do_build():
        log("⏳ Запускаю сборку EXE (это займет пару минут)...", "step")
        ok, msg = await asyncio.get_event_loop().run_in_executor(None, dev_tools.build_exe)
        if ok: log(f"✅ {msg}", "success")
        else: log(f"❌ Ошибка сборки: {msg}", "error")

    async def do_publish():
        ver = dev_version_input.value.strip()
        token = dev_token_input.value.strip()
        if not ver or not token:
            log("❌ Укажи версию и токен", "error")
            return
        exe_path = os.path.join(C.BASE_DIR, "dist", "ProxyCombo.exe")
        log(f"⏳ Публикую релиз v{ver} на GitHub...", "step")
        ok, msg = await asyncio.get_event_loop().run_in_executor(
            None, dev_tools.publish_release, ver, token, exe_path
        )
        if ok: log(f"✅ {msg}", "success")
        else: log(f"❌ Ошибка: {msg}", "error")

    async def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        path = e.files[0].path
        log(f"⏳ Применяю патч {path}...", "step")
        ok, msg = await asyncio.get_event_loop().run_in_executor(
            None, dev_tools.apply_local_patch, path
        )
        if ok: 
            log(f"✅ {msg}", "success")
            log("💡 Перезапусти приложение для применения изменений.", "info")
        else:
            log(f"❌ Ошибка: {msg}", "error")
            
    def pick_patch_file(e):
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["patch"])
'''
    if "async def do_build():" not in app_code:
        app_code = app_code.replace("    # --- DEV TOOLS TAB ---", dev_funcs + "\n    # --- DEV TOOLS TAB ---")

    # Пересоздаем вкладку DevTools
    dev_tab_code = '''    # --- DEV TOOLS TAB ---
    if C.DEV_MODE:
        dev_token_input = ft.TextField(label="GitHub Token", value=GITHUB_TOKEN, password=True, can_reveal_password=True, text_size=12)
        dev_version_input = ft.TextField(label="Версия для релиза", value="1.4.2", text_size=12)

        dev_tab = ft.Column([
            ft.Text("Панель разработчика", size=16, weight=ft.FontWeight.W_700, color=C.PURPLE),
            ft.Text("Управление релизами и патчами", size=11, color=C.SUBTEXT),
            ft.Container(height=10),
            dev_token_input,
            ft.Container(height=10),
            dev_version_input,
            ft.Container(height=10),
            ft.FilledButton("Собрать EXE", icon=ft.Icons.BUILD, on_click=lambda e: asyncio.create_task(do_build())),
            ft.FilledButton("Выпустить релиз на GitHub", icon=ft.Icons.UPLOAD, on_click=lambda e: asyncio.create_task(do_publish())),
            ft.Container(height=20),
            ft.Text("Загрузка патча (.patch)", size=14, color=C.WARNING),
            ft.FilledButton("Выбрать и применить патч", icon=ft.Icons.FILE_DOWNLOAD, on_click=pick_patch_file)
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        
        tabs["pages"].append(dev_tab)
        tabs["labels"].append(("DevTools", ft.Icons.DEVELOPER_MODE))
'''
    # Удаляем старый блок DevTools (от # --- DEV TOOLS TAB --- до tabs["labels"].append)
    app_code = re.sub(r"    # --- DEV TOOLS TAB ---.*?tabs\[\"labels\"\]\.append\(\(\"DevTools\", ft\.Icons\.DEVELOPER_MODE\)\)\n", dev_tab_code, app_code, flags=re.DOTALL)

    with open(app_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(app_code)

    print("✅ Патч v1.4.2 успешно применён!")
    print("💡 Теперь запусти: python main.py --debug")

if __name__ == "__main__":
    main()