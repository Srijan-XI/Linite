# AppImage Support in Linite

## Overview

Linite now supports **AppImage** as a package management fallback mechanism. AppImage is a universal packaging format for Linux that bundles an application and its dependencies into a single executable file.

### Benefits of AppImage Support

- **Zero-dependency apps**: Works on any Linux distro without requiring system packages
- **Easy updates**: Simple to implement app version updates (re-download the AppImage)
- **Portable delivery**: AppImages can be shipped via unofficial channels when no native PM exists
- **Desktop integration**: `.desktop` files are auto-generated so apps appear in application menus
- **Fallback option**: When native PM, Flatpak, and Snap all lack an app, AppImage provides a 3rd-party option

### Supported AppImage Use Cases

AppImage support in Linite is particularly useful for:

1. **Apps with limited package manager support** (e.g., Obsidian, JetBrains Toolbox)
2. **Niche or specialized tools** with small audiences
3. **Pre-release versions** of popular applications
4. **Commercial apps** that may not have official .rpm/.deb packages

---

## Adding AppImage Apps to Linite

### TOML Catalog Entry

Add an `appimage` spec to a software entry in your TOML catalog file:

```toml
# Example: Obsidian (development.toml)
[obsidian]
name = "Obsidian"
description = "Markdown-based note-taking app"
category = "note_taking"
icon = "📔"
website = "https://obsidian.md/"
preferred_pm = "flatpak"  # Flatpak is preferred if available

[obsidian.install_specs.appimage]
packages = ["Obsidian"]  # This becomes the binary name in ~/.local/bin/
script_url = "https://github.com/obsidianmd/obsidian-releases/releases/download/latest/Obsidian-latest-x64.AppImage"
sha256 = "abc123def456..."  # SHA-256 of the AppImage file

[obsidian.install_specs.flatpak]
packages = ["md.obsidian.Obsidian"]
flatpak_remote = "flathub"
```

### Installation Mechanism

When a user installs an app with AppImage support, Linite:

1. **Downloads** the AppImage from the provided `script_url`
2. **Verifies** the SHA-256 checksum (if provided)
3. **Makes it executable** (`chmod +x`)
4. **Moves it** to `~/.local/bin/` (with the binary name specified in `packages`)
5. **Creates a `.desktop` file** in `~/.local/share/applications/` for menu integration

### Installation Flow

```
┌─────────────────────────────────────────┐
│ User selects app for installation       │
└────────────────┬────────────────────────┘
                 ▼
┌─────────────────────────────────────────┐
│ Linite evaluates package managers:      │
│ 1. preferred_pm (if set)                │
│ 2. Native PM (apt/dnf/pacman/zypper)    │
│ 3. Flatpak (if available)               │
│ 4. Snap (if available)                  │
│ 5. AppImage (always available)          │
└────────────────┬────────────────────────┘
                 ▼
       If AppImage is selected...
        
┌─────────────────────────────────────────┐
│ 1. Download AppImage from script_url    │
│ 2. Verify SHA-256 checksum              │
│ 3. Make executable (chmod +x)           │
│ 4. Move to ~/.local/bin/{binary_name}   │
│ 5. Create .desktop file for GUI menus   │
│ 6. Record installation in history       │
└─────────────────────────────────────────┘
```

---

## Example: Full AppImage Entries

### Joplin (Note-taking app)

```toml
[joplin]
name = "Joplin"
description = "Open-source encrypted note-taking app"
category = "note_taking"
icon = "📝"
website = "https://joplinapp.org/"

# Prefer Flatpak if available
[joplin.install_specs.flatpak]
packages = ["net.cozic.joplin_desktop"]
flatpak_remote = "flathub"

# Fallback to AppImage
[joplin.install_specs.appimage]
packages = ["Joplin"]
script_url = "https://github.com/laurent22/joplin/releases/download/v2.14.22/Joplin-2.14.22.AppImage"
sha256 = "e1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd"
```

### JetBrains Toolbox (IDE Manager)

```toml
[jetbrains-toolbox]
name = "JetBrains Toolbox"
description = "IDE manager for IntelliJ, PyCharm, CLion, etc."
category = "development"
icon = "🧰"
website = "https://www.jetbrains.com/toolbox/"

# Only available via AppImage (as of 2024)
[jetbrains-toolbox.install_specs.appimage]
packages = ["JetBrainsToolbox"]
script_url = "https://download.jetbrains.com/toolbox/jetbrains-toolbox-2.0.4.0.tar.gz"
sha256 = "abc123def456..."
post_commands = [
    "cd ~/.local/bin && tar xzf JetBrainsToolbox && rm JetBrainsToolbox"
]
```

---

## User Workflow

### Installation

```bash
# CLI: Install via AppImage fallback
linite --cli install obsidian

# GUI: Select Obsidian → Install
# Linite automatically chooses the best PM (Flatpak > AppImage)
```

### Using the Installed App

```bash
# The app is now in your PATH (if ~/.local/bin is in $PATH)
Obsidian

# If not on PATH, run directly:
~/.local/bin/Obsidian

# The app also appears in your desktop application menu / launcher
```

### Checking Installation

```bash
# Verify the binary exists
ls -la ~/.local/bin/Obsidian

# Check the .desktop file
cat ~/.local/share/applications/obsidian.desktop
```

### Uninstallation

```bash
# Remove the binary and .desktop file
rm ~/.local/bin/Obsidian
rm ~/.local/share/applications/obsidian.desktop

# Linite history also tracks this for potential rollback
```

---

## PATH Configuration

For AppImages to work seamlessly from any terminal, ensure `~/.local/bin` is in your `PATH`:

### For Bash

Add to `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### For Zsh

Add to `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Verify PATH is Set

```bash
echo $PATH | grep -q ~/.local/bin && echo "✓ ~/.local/bin is in PATH" || echo "✗ Not in PATH"
```

---

## Updating AppImage Apps

AppImages must be manually updated (no built-in auto-update in Linite yet).

### Manual Update

1. Check the app website for a new release
2. Run: `linite --cli install obsidian` (re-downloads and overwrites)

### Planned Enhancement

Future versions of Linite will support:
- Version tracking per AppImage
- Auto-detection of outdated AppImages
- One-click update UI for all installed AppImages

---

## Limitations & Considerations

### ✅ Advantages

- Works on any Linux distro
- No system dependencies needed
- Fast, single-file distribution
- Easy to sandbox/isolate (see Firejail)

### ⚠️ Limitations

1. **Manual updates required** — AppImages don't auto-update like native PMs
2. **Desktop integration varies** — Some apps may not respect the generated `.desktop` file
3. **File size** — AppImages tend to be larger than native packages
4. **Library conflicts rare** — But possible if the AppImage uses old glibc versions
5. **No uninstall tracking** — Removing the binary is manual (though history tracks it)

### 🔒 Security

- **Always verify SHA-256** when available
- Download from **official GitHub releases** or trusted sources
- Check **release signatures** if the project provides them
- Be cautious with **3rd-party AppImages** from unknown sources

---

## Troubleshooting

### AppImage won't run

```bash
# 1. Check if it's executable
ls -la ~/.local/bin/Obsidian

# 2. Make it executable if needed
chmod +x ~/.local/bin/Obsidian

# 3. Run directly with verbose output
~/.local/bin/Obsidian --verbose

# 4. Check glibc compatibility (AppImages need glibc 2.29+)
ldd /lib64/libc.so.6 | head -1
```

### App doesn't appear in menu

```bash
# 1. Verify .desktop file exists
ls -la ~/.local/share/applications/obsidian.desktop

# 2. Refresh application cache (GNOME/KDE)
update-desktop-database ~/.local/share/applications/

# 3. Restart your desktop environment or reboot
```

### Checksum mismatch error

```bash
# Means the downloaded file was corrupted or tampered with
# Solutions:
#   1. Check your internet connection
#   2. Retry the installation
#   3. Report the issue on the app's GitHub releases
```

---

## Integration with Other PMs

AppImage works alongside other package managers in a **priority fallback chain**:

```
Preferred PM (if set)
    ↓ (if not available or missing spec)
Native PM (apt/dnf/pacman/zypper)
    ↓ (if not available or missing spec)
Flatpak
    ↓ (if not available or missing spec)
Snap
    ↓ (if not available or missing spec)
AppImage (always available)
```

This means AppImage is **never forced** — it's only used when all other options are exhausted.

---

## Contributing AppImage Entries

To contribute AppImage entries to Linite:

1. **Find a reliable AppImage** (preferably official releases)
2. **Calculate SHA-256**:
   ```bash
   sha256sum ~/Downloads/MyApp.AppImage
   ```
3. **Add entry to TOML**:
   ```toml
   [my_app.install_specs.appimage]
   packages = ["MyApp"]
   script_url = "https://..."
   sha256 = "..."
   ```
4. **Test locally** with `linite --cli install my_app`
5. **Submit a PR** to the Linite repository

---

## See Also

- [AppImage Official Documentation](https://docs.appimage.org/)
- [AppImage Database](https://appimage.github.io/apps/)
- [Linite Catalog Format](./PLUGIN_CATALOG.md)
- [Linite Installation Guide](../README.md)
