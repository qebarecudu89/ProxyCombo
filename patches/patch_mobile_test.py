import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔧 Принудительное внедрение Mobile Mode (ТЕСТ)...")

    # 1. Внедряем переменную и функции в app.py
    app_path = os.path.join(ROOT, "proxycombo", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    if "import random" not in app_code:
        app_code = app_code.replace("import time", "import time\nimport random")

    # Принудительно добавляем switch, если его нет
    if "mobile_switch =" not in app_code:
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

    # Удаляем старые блоки мобильной эмуляции, если они где-то застряли
    app_code = re.sub(r'if state\.get\("mobile_emulation", False\):.*?hooks\.run\("before_chrome_launch", chrome_args, urls, log\)', 'hooks.run("before_chrome_launch", chrome_args, urls, log)', app_code, flags=re.DOTALL)

    # Внедряем генератор строго перед запуском
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
    
    app_code = app_code.replace('            hooks.run("before_chrome_launch", chrome_args, urls, log)', mobile_block)

    with open(app_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(app_code)

    # 2. ГАРАНТИРОВАННО добавляем кнопку в UI (в ui/tabs.py)
    tabs_path = os.path.join(ROOT, "proxycombo", "ui", "tabs.py")
    with open(tabs_path, "r", encoding="utf-8") as f:
        tabs_code = f.read()

    if 'ctx["mobile_switch"]' not in tabs_code:
        # Вставляем прямо после WebRTC, не надейся на пробелы, ищем по ключевому слову
        tabs_code = tabs_code.replace(
            'ctx["webrtc_switch"],',
            'ctx["webrtc_switch"],\n'
            '                                ft.Text("Mobile Mode (ТЕСТ)", size=10, color=C.WARNING),\n'
            '                                ctx["mobile_switch"],'
        )
        # Если WebRTC не нашли, ставим после кнопки теста прокси
        if 'ctx["mobile_switch"]' not in tabs_code:
            tabs_code = tabs_code.replace(
                'ctx["test_proxy_btn"],',
                'ctx["test_proxy_btn"],\n'
                '                                ft.Text("Mobile Mode (ТЕСТ)", size=10, color=C.WARNING),\n'
                '                                ctx["mobile_switch"],'
            )
            
        with open(tabs_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(tabs_code)

    print("✅ Тестовый патч применён! Версия осталась 1.4.1.")
    print("💡 Запусти python main.py --debug и проверь наличие тумблера 'Mobile Mode (ТЕСТ)'")

if __name__ == "__main__":
    main()