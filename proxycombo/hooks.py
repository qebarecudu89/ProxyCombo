from .logging_utils import file_log

HOOKS = {
    "before_relay_start": [],
    "after_relay_ready": [],
    "before_chrome_launch": [],
    "after_clean": [],
    "on_rotation": [],
    "custom_tab": [],
    "custom_action_button": [],
}

def register(name: str, func):
    HOOKS.setdefault(name, []).append(func)

def run(name: str, *args, **kwargs):
    for fn in HOOKS.get(name, []):
        try:
            fn(*args, **kwargs)
        except Exception as e:
            file_log(f"hook '{name}' failed: {e}")