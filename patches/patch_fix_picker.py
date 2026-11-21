import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔧 Убираем FilePicker и ставим нативный диалог (tkinter)...")

    app_path = os.path.join(ROOT, "proxycombo", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    # 1. Удаляем все следы FilePicker из кода
    app_code = app_code.replace('file_picker = ft.FilePicker(on_result=lambda e: asyncio.create_task(on_file_picked(e)))', '')
    app_code = app_code.replace('page.overlay.append(file_picker)', '')

    # 2. Меняем функцию on_file_picked и pick_patch_file
    old_picker = '''    async def on_file_picked(e: ft.FilePickerResultEvent):
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
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["patch"])'''

    new_picker = '''    async def apply_patch_from_path(path):
        if not path:
            return
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
        # Нативный диалог Windows через tkinter
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw() # Скрываем главное окно tkinter
        root.attributes("-topmost", True)
        
        path = filedialog.askopenfilename(
            title="Выберите файл патча",
            filetypes=[("Patch files", "*.patch"), ("All files", "*.*")]
        )
        root.destroy()
        
        if path:
            dev_patch_input.value = path
            page.update()
            asyncio.create_task(apply_patch_from_path(path))'''

    app_code = app_code.replace(old_picker, new_picker)

    # 3. Обновляем UI DevTools (добавляем поле ввода и меняем кнопку)
    old_ui = '''            ft.Container(height=20),
            ft.Text("Загрузка патча (.patch)", size=14, color=C.WARNING),
            ft.FilledButton("Выбрать и применить патч", icon=ft.Icons.FILE_DOWNLOAD, on_click=pick_patch_file)'''
    
    new_ui = '''            ft.Container(height=20),
            ft.Text("Загрузка патча (.patch)", size=14, color=C.WARNING),
            dev_patch_input,
            ft.FilledButton("Выбрать файл и применить", icon=ft.Icons.FILE_DOWNLOAD, on_click=pick_patch_file),
            ft.FilledButton("Применить введенный путь", icon=ft.Icons.PLAY_ARROW, on_click=lambda e: asyncio.create_task(apply_patch_from_path(dev_patch_input.value.strip())))'''
    
    app_code = app_code.replace(old_ui, new_ui)

    # Объявляем dev_patch_input, если его нет
    if "dev_patch_input =" not in app_code:
        app_code = app_code.replace(
            "dev_version_input = ft.TextField(label=\"Версия для релиза\", value=\"1.4.2\", text_size=12)",
            "dev_version_input = ft.TextField(label=\"Версия для релиза\", value=\"1.4.2\", text_size=12)\n        dev_patch_input = ft.TextField(label=\"Путь к файлу .patch\", text_size=12)"
        )

    with open(app_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(app_code)

    print("✅ FilePicker удален, нативный выбор файлов работает!")
    print("💡 Запусти: python main.py --debug")

if __name__ == "__main__":
    main()