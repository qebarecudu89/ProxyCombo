import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_F = os.path.join(ROOT, "version.py")
BACKUP_DIR = os.path.join(ROOT, "patches", ".backup")
MANIFEST = os.path.join(ROOT, "patches", ".last_patch.json")

def read_version():
    ns = {}
    with open(VERSION_F, "r", encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns["VERSION"]

def write_version(v):
    src = open(VERSION_F, "r", encoding="utf-8").read()
    src = re.sub(r'^VERSION\\s*=\\s*"[^"]+"', f'VERSION = "{v}"',
                 src, count=1, flags=re.M)
    open(VERSION_F, "w", encoding="utf-8").write(src)

def files_in_patch(patch_path):
    files = []
    with open(patch_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("--- a/") or line.startswith("+++ b/"):
                path = line[6:].strip().split("\\t")[0]
                if path and path != "/dev/null":
                    files.append(path)
    return sorted(set(files))

def backup(files):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for f in os.listdir(BACKUP_DIR):
        try:
            os.remove(os.path.join(BACKUP_DIR, f))
        except Exception:
            pass
    for rel in files:
        src = os.path.join(ROOT, rel)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(BACKUP_DIR, rel.replace("/", "__")))

def restore_backup():
    if not os.path.isdir(BACKUP_DIR):
        return False
    for name in os.listdir(BACKUP_DIR):
        rel = name.replace("__", "/")
        shutil.copy2(os.path.join(BACKUP_DIR, name), os.path.join(ROOT, rel))
    return True

def try_apply(patch_path):
    r = subprocess.run(
        ["patch", "-p1", "--dry-run", "--forward", "-i", patch_path],
        cwd=ROOT, capture_output=True, text=True,
    )
    if r.returncode == 0:
        r = subprocess.run(
            ["patch", "-p1", "--forward", "-i", patch_path],
            cwd=ROOT, capture_output=True, text=True,
        )
        return r.returncode == 0, r.stderr
    r2 = subprocess.run(["git", "apply", "--check", patch_path],
                        cwd=ROOT, capture_output=True, text=True)
    if r2.returncode == 0:
        r2 = subprocess.run(["git", "apply", patch_path],
                            cwd=ROOT, capture_output=True, text=True)
        return r2.returncode == 0, r2.stderr
    return False, r.stderr or r2.stderr or "патч не применим"

def compile_check():
    r = subprocess.run([sys.executable, "-m", "compileall", "-q", ROOT],
                       capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr)[:1500]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patch", nargs="?", help="путь к .patch файлу")
    ap.add_argument("--rollback", action="store_true",
                    help="откатить последний патч")
    args = ap.parse_args()

    if args.rollback:
        ok = restore_backup()
        print("✅ Откат выполнен" if ok else "⚠️ Бэкапа нет")
        return

    if not args.patch or not os.path.exists(args.patch):
        print("❌ Укажи существующий .patch файл")
        sys.exit(1)

    old_ver = read_version()
    print(f"📦 Текущая версия: {old_ver}")

    files = files_in_patch(args.patch)
    backup(files)
    print(f"🗄  Бэкап {len(files)} файлов → patches/.backup/")

    ok, err = try_apply(args.patch)
    if not ok:
        print(f"❌ Патч не применился:\\n{err}")
        restore_backup()
        sys.exit(2)

    ok, err = compile_check()
    if not ok:
        print(f"❌ После патча код не компилируется:\\n{err}")
        print("↩️  Откатываю...")
        restore_backup()
        sys.exit(3)

    base = os.path.splitext(os.path.basename(args.patch))[0]
    parts = base.split("__")
    new_ver = parts[-1].lstrip("v") if len(parts) >= 2 else old_ver
    write_version(new_ver)

    json.dump({"applied_at": time.strftime("%Y-%m-%d %H:%M:%S"),
               "from": old_ver, "to": new_ver, "patch": args.patch},
              open(MANIFEST, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"✅ Применено: {old_ver} → {new_ver}")
    print("💡 Проверь: python main.py --debug")

if __name__ == "__main__":
    main()