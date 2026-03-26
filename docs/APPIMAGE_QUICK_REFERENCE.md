# AppImage Support - Quick Reference

## For Users

### Installing an AppImage App

```bash
# Install via Linite CLI
linite --cli install obsidian

# Or use GUI
# → Select app → Click Install
# → Linite automatically picks the best package manager (Flatpak > AppImage)
```

### Using Installed AppImage Apps

```bash
# From any terminal (if ~/.local/bin is in PATH)
Obsidian

# Get full path
which Obsidian
# Output: ~/.local/bin/Obsidian

# Check if installed
ls ~/.local/bin/Obsidian
```

### Uninstalling

```bash
# Remove binary and .desktop file
rm ~/.local/bin/Obsidian
rm ~/.local/share/applications/obsidian.desktop

# Or use Linite history to rollback
linite --rollback  # undoes the last installation
```

### Ensuring ~/.local/bin is in PATH

```bash
# Check if it's in PATH
echo $PATH | grep ~/.local/bin

# If not, add to ~/.bashrc or ~/.zshrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## For Contributors

### Adding a New AppImage Entry

#### Step 1: Find the AppImage

Search the GitHub releases for your app:
- Most apps provide direct `.AppImage` download links
- Look for `*-x64.AppImage` or similar files

#### Step 2: Generate the Catalog Entry

Use the AppImage helper:

```bash
python utils/appimage_helper.py generate \
  obsidian "Obsidian" \
  "https://obsidian.md" \
  "https://github.com/obsidianmd/obsidian-releases/releases/download/latest/Obsidian-latest-x64.AppImage" \
  --icon "🔮"
```

This will output the TOML entry to copy/paste into the catalog.

#### Step 3: Add to Catalog

Edit the appropriate TOML file in `data/catalog/`:

```toml
[apps.install_specs.appimage]
packages = ["Obsidian"]
script_url = "https://github.com/.../Obsidian-latest-x64.AppImage"
sha256 = "abc123def456..."
```

#### Step 4: Test

```bash
# Test the installation
linite --cli install obsidian

# Verify it works
Obsidian --version

# Check the .desktop file
cat ~/.local/share/applications/obsidian.desktop

# Remove for cleanup
linite --rollback
```

---

## Common AppImage Apps

### Ready to Add

| App | URL | Status |
|---|---|---|
| **Obsidian** | https://github.com/obsidianmd/obsidian-releases | ✅ Done |
| **Joplin** | https://github.com/laurent22/joplin | ✅ Done |
| **Logseq** | https://github.com/logseq/logseq | ✅ Done |
| **Headlamp** | https://github.com/kinvolk/headlamp | ⏳ TODO |
| **CherryTree** | https://github.com/giuspen/cherrytree | ⏳ TODO |

### Recommended AppImage-Only Apps

- **Obsidian** — Markdown note-taking (preferred PM: Flatpak, fallback: AppImage)
- **JetBrains Toolbox** — IDE manager (AppImage only)
- **Headlamp** — Kubernetes UI (AppImage recommended)
- **Insync** — Cloud sync client (AppImage only)
- **draw.io** — Diagramming tool (AppImage available)

---

## Troubleshooting

### "AppImage not executable"

```bash
# Make it executable
chmod +x ~/.local/bin/Obsidian

# Test directly
~/.local/bin/Obsidian --help
```

### "glibc" compatibility error

```bash
# Check your glibc version (AppImages need 2.29+)
ldd --version

# If too old, your distro may be too old for this AppImage
# Try a different version or use native PM instead
```

### "App doesn't appear in menu"

```bash
# Refresh desktop database
update-desktop-database ~/.local/share/applications/

# Or manually verify the .desktop file
cat ~/.local/share/applications/obsidian.desktop

# Check required fields are present:
# Name=, Exec=, Type=Application, Icon=, Terminal=false
```

### "SHA-256 mismatch"

```bash
# File was corrupted, try again:
linite --cli install obsidian

# Or verify manually:
python utils/appimage_helper.py verify \
  ~/.local/bin/Obsidian \
  abc123def456...
```

---

## Implementation Details

### Installation Flow

```
User requests install
    ↓
Linite picks PM (native → flatpak → snap → appimage)
    ↓
If AppImage chosen:
    ├─ Download from script_url
    ├─ Verify SHA-256 (if provided)
    ├─ Move to ~/.local/bin/{binary_name}
    ├─ chmod +x (make executable)
    ├─ Create ~/.local/share/applications/{app_id}.desktop
    └─ Record in history
```

### File Locations

```
~/.local/bin/Obsidian                           # The executable
~/.local/share/applications/obsidian.desktop    # Menu integration
~/.local/share/linite/history/...               # Installation history
```

### .desktop File Format

```ini
[Desktop Entry]
Name=Obsidian
Exec=~/.local/bin/Obsidian %U
Type=Application
Categories=Utility;
Icon=obsidian
Terminal=false
Path=~/.local/bin
```

---

## See Also

- [Full AppImage Support Documentation](./APPIMAGE_SUPPORT.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [AppImage Official Docs](https://docs.appimage.org/)
- [FreeDesktop .desktop Format](https://specifications.freedesktop.org/desktop-entry-spec/)
