import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔧 Установка патча v1.4.1 (Fix Yandex + Mobile Spoofing)...")

    # 1. Бамп версий до 1.4.1
    v_path = os.path.join(ROOT, "version.py")
    with open(v_path, "r", encoding="utf-8") as f: v_content = f.read()
    v_content = re.sub(r'VERSION = ".*?"', 'VERSION = "1.4.1"', v_content)
    with open(v_path, "w", encoding="utf-8", newline="\n") as f: f.write(v_content)

    c_path = os.path.join(ROOT, "proxycombo", "config.py")
    with open(c_path, "r", encoding="utf-8") as f: c_content = f.read()
    c_content = re.sub(r'CURRENT_VERSION = ".*?"', 'CURRENT_VERSION = "1.4.1"', c_content)
    with open(c_path, "w", encoding="utf-8", newline="\n") as f: f.write(c_content)

    # 2. Фикс процессов Яндекс.Браузера в config.py
    old_yandex = '''    "yandex": {
        "title": "Yandex Browser",
        "exe": "browser.exe",
        "processes": ["browser.exe", "yandex_browser.exe"],'''
    new_yandex = '''    "yandex": {
        "title": "Yandex Browser",
        "exe": "browser.exe",
        "processes": ["browser.exe", "yandex_browser.exe", "yandexbrowser.exe", "yandex_browser_process.exe"],'''
    c_content = c_content.replace(old_yandex, new_yandex)

    # Добавляем пути для Yandex (если не хватает)
    if r"%LOCALAPPDATA%\\Yandex\\YandexBrowser\\Application\\browser.exe" not in c_content:
        old_paths = '''        "paths": [
            r"C:\\\\Program Files\\\\Yandex\\\\YandexBrowser\\\\Application\\\\browser.exe",
            r"C:\\\\Program Files (x86)\\\\Yandex\\\\YandexBrowser\\\\Application\\\\browser.exe",
        ],'''
        new_paths = '''        "paths": [
            r"C:\\\\Program Files\\\\Yandex\\\\YandexBrowser\\\\Application\\\\browser.exe",
            r"C:\\\\Program Files (x86)\\\\Yandex\\\\YandexBrowser\\\\Application\\\\browser.exe",
            r"%LOCALAPPDATA%\\\\Yandex\\\\YandexBrowser\\\\Application\\\\browser.exe",
        ],'''
        c_content = c_content.replace(old_paths, new_paths)

    with open(c_path, "w", encoding="utf-8", newline="\n") as f: f.write(c_content)

    # 3. Внедряем мобильную эмуляцию в app.py
    app_path = os.path.join(ROOT, "proxycombo", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    # Добавляем import random (если нет)
    if "import random" not in app_code:
        app_code = app_code.replace("import time", "import time\nimport random")

    # Переключатель Mobile Mode
    if "mobile_switch = ft.Switch" not in app_code:
        app_code = app_code.replace(
            'webrtc_switch = ft.Switch(value=state.get("webrtc_block", True), active_color=C.SUCCESS)',
            'webrtc_switch = ft.Switch(value=state.get("webrtc_block", True), active_color=C.SUCCESS)\n'
            '    mobile_switch = ft.Switch(value=state.get("mobile_emulation", False), active_color=C.WARNING)'
        )
        
        app_code = app_code.replace(
            'webrtc_switch.on_change = on_webrtc_change',
            'webrtc_switch.on_change = on_webrtc_change\n\n'
            '    def on_mobile_change(e):\n'
            '        state["mobile_emulation"] = e.control.value\n'
            '        state_mod.save_state(state)\n'
            '    mobile_switch.on_change = on_mobile_change'
        )

        app_code = app_code.replace(
            '"webrtc_switch": webrtc_switch,',
            '"webrtc_switch": webrtc_switch, "mobile_switch": mobile_switch,'
        )

    # Генератор Android-отпечатков
    mobile_block = '''            if state.get("mobile_emulation", False):
                devices = [
                    ("Samsung Galaxy S23", "SM-S911B"), ("Samsung Galaxy S22", "SM-S901B"),
                    ("Google Pixel 7", "Pixel 7"), ("Google Pixel 6", "Pixel 6"),
                    ("Xiaomi 13 Pro", "2210132G"), ("Xiaomi Redmi Note 12", "22111317G"),
                    ("OnePlus 11", "CPH2449"), ("OnePlus 10 Pro", "NE2213"),
                    ("Sony Xperia 1 IV", "XQ-CT54"), ("Asus ROG Phone 6", "AI2201"),
                ]
                android_versions = ["11", "12", "13", "14"]
                chrome_versions = ["114.0.5735.196", "115.0.5790.166", "116.0.5845.163", "117.0.5938.60", "118.0.5993.80"]
                
                dev_name, dev_model = random.choice(devices)
                os_ver = random.choice(android_versions)
                chrome_ver = random.choice(chrome_versions)
                
                ua = f"Mozilla/5.0 (Linux; Android {os_ver}; {dev_model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36"
                
                log(f"📱 Мобильный отпечаток: {dev_name} (Android {os_ver}, Chrome {chrome_ver.split('.')[0]})", "info")
                
                chrome_args.append(f"--user-agent={ua}")
                chrome_args.append("--touch-events=enabled")
                chrome_args.append("--enable-mobile-emulation")
                chrome_args.append("--window-size=390,844")
            
            hooks.run("before_chrome_launch", chrome_args, urls, log)'''
    
    # Удаляем старые попытки вставить мобильный режим, если они были
    app_code = re.sub(r'if state\.get\("mobile_emulation", False\):.*?hooks\.run\("before_chrome_launch", chrome_args, urls, log\)', mobile_block, app_code, flags=re.DOTALL)

    with open(app_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(app_code)

    # 4. Выводим переключатель в UI
    tabs_path = os.path.join(ROOT, "proxycombo", "ui", "tabs.py")
    with open(tabs_path, "r", encoding="utf-8") as f:
        tabs_code = f.read()

    if 'ctx["mobile_switch"]' not in tabs_code:
        tabs_code = tabs_code.replace(
            'ctx["webrtc_switch"],',
            'ctx["webrtc_switch"],\n'
            '                                ft.Text("Mobile Mode", size=10, color=C.TEXT_DIM),\n'
            '                                ctx["mobile_switch"],'
        )
        with open(tabs_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(tabs_code)

    print("✅ Патч v1.4.1 успешно применён!")
    print("💡 Запусти: python main.py --debug")
    print("💡 Проверь выбор Yandex и работу мобильного режима.")

if __name__ == "__main__":
    main()