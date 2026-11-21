import os
import sys
import tempfile

IS_FROZEN = getattr(sys, "frozen", False)
BASE_DIR = (
    os.path.dirname(sys.executable) if IS_FROZEN
    else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

URLS_FILE = os.path.join(BASE_DIR, "urls.txt")
GOST_EXE = os.path.join(BASE_DIR, "gost.exe")
SINGBOX_EXE = os.path.join(BASE_DIR, "sing-box.exe")
SINGBOX_CONFIG = os.path.join(BASE_DIR, "singbox-config.json")
LOG_FILE = os.path.join(BASE_DIR, "chrome_cleaner.log")
STATE_FILE = os.path.join(BASE_DIR, "chrome_cleaner_state.json")
SYS_PROXY_BACKUP = os.path.join(BASE_DIR, "system_proxy_backup.json")
FIRST_RUN_FLAG = os.path.join(BASE_DIR, "first_run.flag")

LOCAL_PORT = 1080
LOCAL_HTTP_PORT = 1081
SINGBOX_VERSION = "1.14.2"
ROTATION_COOLDOWN = 120

TEMP_PROFILE = os.path.join(
    os.environ.get("TEMP", tempfile.gettempdir()),
    "chrome_cleaner_profile",
)


# ---- Браузеры ----
BROWSERS = {
    "chrome": {
        "title": "Google Chrome",
        "exe": "chrome.exe",
        "processes": ["chrome.exe"],
        "paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
        ],
        "user_data": r"%LOCALAPPDATA%\Google\Chrome\User Data",
        "registry": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
    },
    "yandex": {
        "title": "Yandex Browser",
        "exe": "browser.exe",
        "processes": ["browser.exe", "yandex_browser.exe", "yandexbrowser.exe", "yandex_browser_process.exe"],
        "paths": [
            r"C:\Program Files\Yandex\YandexBrowser\Application\browser.exe",
            r"C:\Program Files (x86)\Yandex\YandexBrowser\Application\browser.exe",
            r"%LOCALAPPDATA%\Yandex\YandexBrowser\Application\browser.exe",
        ],
        "user_data": r"%LOCALAPPDATA%\Yandex\YandexBrowser\User Data",
        "registry": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\browser.exe",
    },
}

DEFAULT_BROWSER = "chrome"
TEMP_PROFILE_YANDEX = os.path.join(
    os.environ.get("TEMP", tempfile.gettempdir()),
    "yandex_cleaner_profile",
)

BG_DEEP = "#1a1a22"
BG = "#22222e"
BG_CARD = "#2a2a38"
BG_INPUT = "#252532"
BG_TITLEBAR = "#1e1e28"
BORDER = "#35354a"
BORDER_SOFT = "#2e2e40"
TEXT = "#f0f0f5"
TEXT_DIM = "#b0b0c0"
SUBTEXT = "#707080"
PURPLE = "#9b6dff"
PINK = "#e879f9"
NEON = "#a78bfa"
CYAN = "#67e8f9"
SUCCESS = "#4ade80"
WARNING = "#fbbf24"
DANGER = "#f87171"
ORANGE = "#fb923c"
GRAD_PURPLE = [PURPLE, PINK]
GRAD_NEON = ["#a78bfa", "#67e8f9"]
GRAD_PINK = ["#e879f9", "#9b6dff"]

CREATE_NO_WINDOW = 0x08000000

# ---- Обновления ----
GITHUB_REPO = "qebarecudu89/ProxyCombo"
GITHUB_TOKEN = "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"  
CURRENT_VERSION = "1.4.2"

# ---- Защита ----
SPOOF_TIMEZONE = False
BLOCK_WEBRTC = True

# ---- Профили и Прокси ----
PROFILES_FILE = os.path.join(BASE_DIR, "profiles.json")
PROXY_POOL_FILE = os.path.join(BASE_DIR, "proxy_pool.txt")
AUTO_ROTATE_MINUTES = 0 # 0 = выкл


# Режим разработчика
DEV_MODE = True
