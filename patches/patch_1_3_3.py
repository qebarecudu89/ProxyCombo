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

def main():
    print("🔧 Полная очистка кода обновлений (v1.3.3)...")

    # 1. Бамп версии
    replace_in_file("version.py", 'VERSION = "1.3.2"', 'VERSION = "1.3.3"')
    replace_in_file("proxycombo/config.py", 'CURRENT_VERSION = "1.3.2"', 'CURRENT_VERSION = "1.3.3"')

    # 2. Чистим app.py от старых остатков и вставляем чистый блок
    path = os.path.join(ROOT, "proxycombo/app.py")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Вырезаем всё, что связано с обновлениями, если оно осталось от прошлых патчей
    import re
    # Удаляем старые блоки
    content = re.sub(r"    update_info = \{.*?\n\n    async def check_updates_on_start\(\):.*?\n\n    page\.run_task\(check_updates_on_start\)", "", content, flags=re.DOTALL)
    content = re.sub(r"    async def check_updates_on_start\(\):.*?\n\n    page\.run_task\(check_updates_on_start\)", "", content, flags=re.DOTALL)
    
    # Убираем старую кнопку из Layout, если она там осталась
    content = content.replace("ft.Container(content=ft.Row([build_status_bar(status_dot, status_text, ip_text), update_btn]),", "ft.Container(content=ft.Row([build_status_bar(status_dot, status_text, ip_text), update_btn_ref.current if update_btn_ref.current else ft.Container()]),")
    
    # Вставляем новый, чистый блок с Ref
    clean_block = '''    update_info = {"version": None, "url": None}
    update_btn_ref = ft.Ref[ft.Container]()

    async def check_updates_on_start():
        latest, url = await asyncio.get_event_loop().run_in_executor(None, check_for_updates)
        if latest:
            update_info["version"] = latest
            update_info["url"] = url
            log(f"🚀 Доступно обновление: v{latest} (текущая: v{C.CURRENT_VERSION})", "warn")
            if update_btn_ref.current:
                update_btn_ref.current.content.value = f"Обновить до v{latest}"
                update_btn_ref.current.visible = True
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

    page.run_task(check_updates_on_start)
'''
    # Вставляем перед update_status_from_state()
    content = content.replace("    update_status_from_state()\n", clean_block + "\n    update_status_from_state()\n", 1)

    # Убеждаемся, что в Layout создается кнопка с Ref
    layout_old = '''            ft.Container(
                content=ft.Row([build_status_bar(status_dot, status_text, ip_text), update_btn_ref.current if update_btn_ref.current else ft.Container()]),
                padding=ft.Padding.symmetric(horizontal=14, vertical=4),
                bgcolor=C.BG_TITLEBAR,
            ),'''
    
    layout_new = '''            ft.Container(
                content=ft.Row([
                    build_status_bar(status_dot, status_text, ip_text),
                    ft.Container(
                        content=ft.Text("Обновить", size=11, color="white", weight=ft.FontWeight.W_700),
                        padding=ft.Padding.symmetric(vertical=8, horizontal=16),
                        bgcolor=C.SUCCESS, border_radius=8,
                        on_click=lambda e: asyncio.create_task(do_update(e)),
                        visible=False,
                        ref=update_btn_ref,
                    )
                ]),
                padding=ft.Padding.symmetric(horizontal=14, vertical=4),
                bgcolor=C.BG_TITLEBAR,
            ),'''
    
    content = content.replace(layout_old, layout_new)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    print("✅ Патч v1.3.3 успешно применён! Код полностью очищен.")
    print("💡 Запусти: python main.py --debug")

if __name__ == "__main__":
    main()