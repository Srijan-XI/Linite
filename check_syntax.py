import ast, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
files = [
    "main.py",
    "gui/app.py",
    "gui/styles.py",
    "gui/components/__init__.py",
    "gui/components/software_panel.py",
    "gui/components/category_panel.py",
    "gui/components/progress_panel.py",
    "gui/components/preset_panel.py",
    "gui/components/app_detail.py",
    "core/__init__.py",
    "core/installer.py",
    "core/uninstaller.py",
    "core/history.py",
    "core/profiles.py",
    "core/distro.py",
    "core/updater.py",
    "core/package_manager.py",
    "data/__init__.py",
    "data/presets.py",
    "data/software_catalog.py",
    "utils/__init__.py",
    "utils/helpers.py",
]
ok = True
for f in files:
    try:
        ast.parse(open(f, encoding="utf-8").read())
        print(f"OK  {f}")
    except SyntaxError as e:
        print(f"ERR {f}: {e}")
        ok = False
sys.exit(0 if ok else 1)
