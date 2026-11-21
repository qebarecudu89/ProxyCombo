import os

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
    print("🔧 Исправляю ошибку с update_btn (v1.3.1)...")

    # 1. Бамп версии
    replace_in_file("version.py", 'VERSION = "1.3.0"', 'VERSION = "1.3.1"')
    replace_in_file("proxycombo/config.py", 'CURRENT_VERSION = "1.3.0"', 'CURRENT_VERSION = "1.3.1"')

    # 2. Исправление порядка переменных в app.py
    old_block = '''    update_info = {"version": None, "url": None}

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

    new_block = '''    update_info = {"version": None, "url": None}
    update_btn = ft.Container(
        content=ft.Text("Обновить", size=11, color="white", weight=ft.FontWeight.W_700),
        padding=ft.Padding.symmetric(vertical=8, horizontal=16),
        bgcolor=C.SUCCESS, border_radius=8,
        on_click=lambda e: asyncio.create_task(do_update(e)),
        visible=False,
    )

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

    page.run_task(check_updates_on_start)'''

    if replace_in_file("proxycombo/app.py", old_block, new_block):
        print("✅ Патч v1.3.1 успешно применён!")
        print("💡 Запусти: python main.py --debug")
    else:
        print("⚠️  Блок кода для замены не найден. Возможно, структура файла отличается.")

if __name__ == "__main__":
    main()