import ast, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
files = [
    "gui/app.py",
    "core/installer.py",
    "core/uninstaller.py",
    "core/history.py",
    "core/profiles.py",
    "gui/components/software_panel.py",
    "gui/components/app_detail.py",
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
