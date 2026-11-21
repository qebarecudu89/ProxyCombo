import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔧 Восстанавливаю структуру app.py (v1.3.4)...")
    path = os.path.join(ROOT, "proxycombo", "app.py")
    
    if not os.path.exists(path):
        print("❌ Файл proxycombo/app.py не найден!")
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Бамп версий
    v_path = os.path.join(ROOT, "version.py")
    with open(v_path, "r", encoding="utf-8") as f: v_content = f.read()
    v_content = re.sub(r'VERSION = "1\.3\.\d"', 'VERSION = "1.3.5"', v_content)
    with open(v_path, "w", encoding="utf-8", newline="\n") as f: f.write(v_content)

    c_path = os.path.join(ROOT, "proxycombo", "config.py")
    with open(c_path, "r", encoding="utf-8") as f: c_content = f.read()
    c_content = re.sub(r'CURRENT_VERSION = "1\.3\.\d"', 'CURRENT_VERSION = "1.3.5"', c_content)
    with open(c_path, "w", encoding="utf-8", newline="\n") as f: f.write(c_content)

    # 2. Вычищаем любой старый мусор с update_btn и check_updates
    # Удаляем любые попытки объявить update_btn_ref или update_info
    content = re.sub(r"[ \t]*update_info = \{.*?\n", "", content)
    content = re.sub(r"[ \t]*update_btn_ref = ft\.Ref.*?\n", "", content)
    
    # Удаляем старые функции обновлений
    content = re.sub(r"[ \t]*async def check_updates_on_start\(\):.*?(?=def |async def |page\.run_task|\Z)", "", content, flags=re.DOTALL)
    content = re.sub(r"[ \t]*async def do_update\(e\):.*?(?=def |async def |page\.run_task|\Z)", "", content, flags=re.DOTALL)
    content = re.sub(r"[ \t]*page\.run_task\(check_updates_on_start\)\n", "", content)

    # Убираем старую кнопку из layout, если она там была
    content = content.replace("update_btn_ref.current if update_btn_ref.current else ft.Container()", "ft.Container()")
    
    # Ищем место в layout, куда надо вставить кнопку
    # В нашем layout есть строка с build_status_bar
    layout_old = '''ft.Container(
                content=ft.Row([build_status_bar(status_dot, status_text, ip_text), ft.Container()]),
                padding=ft.Padding.symmetric(horizontal=14, vertical=4),
                bgcolor=C.BG_TITLEBAR,
            ),'''
    
    layout_new = '''ft.Container(
                content=ft.Row([build_status_bar(status_dot, status_text, ip_text), update_btn]),
                padding=ft.Padding.symmetric(horizontal=14, vertical=4),
                bgcolor=C.BG_TITLEBAR,
            ),'''
    content = content.replace(layout_old, layout_new)

    # 3. Вставляем чистый блок инициализации ПЕРЕД page.add(...)
    # Найдем конец функции main (перед page.add)
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
    
    # Вставляем перед page.add
    if "page.add(" in content:
        content = content.replace("    page.add(", clean_init + "\n    page.add(", 1)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    print("✅ Структура восстановлена! Версия 1.3.5")
    print("💡 Запусти: python main.py --debug")

if __name__ == "__main__":
    main()