# Plugin / Drop-In Catalog Guide

Linite's **plugin catalog** feature allows you to define custom applications without modifying the main codebase. This is perfect for:

- **Teams** distributing internal tools
- **Enterprise** environments with proprietary software
- **Power users** adding niche applications
- **Testing** new app definitions before contributing upstream

---

## Quick Start

### 1. Create the catalog directory

```bash
mkdir -p ~/.config/linite/catalog
```

On Windows, this is typically:
```
%USERPROFILE%\.config\linite\catalog\
```

### 2. Create a TOML file

Create any `.toml` file in that directory (e.g., `my_apps.toml`):

```toml
[[apps]]
id          = "my-tool"
name        = "My Custom Tool"
description = "Internal company tool"
category    = "Development"
icon        = "🔧"
website     = "https://internal.company.com/tools/my-tool"
preferred_pm = "snap"

[apps.install_specs.snap]
packages = ["my-tool"]
```

### 3. Launch Linite

Your custom apps will automatically appear in the catalog!

```bash
linite
```

---

## Features

### ✅ Multiple catalog files
You can organize your apps into multiple `.toml` files:
```
~/.config/linite/catalog/
├── company_tools.toml
├── experimental.toml
└── custom_overrides.toml
```

### ✅ Override built-in apps
If your catalog defines an app with an ID that already exists (e.g., `"git"`), your version **replaces** the built-in one. This lets you:
- Use custom repositories
- Add company-specific configuration
- Change installation methods

### ✅ All package managers supported
Your custom apps support all the same package managers as built-in apps:
- `apt`, `dnf`, `pacman`, `zypper` (native package managers)
- `snap`, `flatpak` (universal packages)
- `script` (custom installation scripts)

### ✅ Pre/post-install commands
Add custom setup steps before or after installation:
```toml
[apps.install_specs.apt]
packages = ["my-tool"]
pre_commands = [
  "wget -qO- https://repo.example.com/key.gpg | apt-key add -",
  "add-apt-repository 'deb https://repo.example.com/apt stable main'",
  "apt-get update"
]
post_commands = [
  "systemctl enable my-tool",
  "my-tool --setup"
]
```

---

## Full App Schema

Here's the complete structure of an app definition:

```toml
[[apps]]
# ── Required fields ──
id          = "unique-slug"         # Must be unique, lowercase-with-dashes
name        = "Display Name"
description = "Short description shown in the GUI"
category    = "Category Name"       # Must match an existing or new category

# ── Optional fields ──
icon        = "🚀"                 # Emoji icon (default: 📦)
website     = "https://..."        # Homepage URL
preferred_pm = "snap"              # Preferred package manager: apt|dnf|pacman|zypper|snap|flatpak|script

# ── Installation specs (at least one required) ──

# Native package managers
[apps.install_specs.apt]
packages = ["pkg-name"]
pre_commands = []    # Optional: run before install
post_commands = []   # Optional: run after install

[apps.install_specs.dnf]
packages = ["pkg-name"]

[apps.install_specs.pacman]
packages = ["pkg-name"]

[apps.install_specs.zypper]
packages = ["pkg-name"]

# Universal packages
[apps.install_specs.snap]
packages = ["snap-name"]
snap_classic = false  # Set to true if app requires --classic

[apps.install_specs.flatpak]
packages = ["com.example.AppId"]
flatpak_remote = "flathub"  # Or another remote

# Script-based installation
[apps.install_specs.script]
script_url = "https://example.com/install.sh"
sha256 = "abc123..."  # Optional but recommended for security
pre_commands = []
post_commands = []

# Universal fallback (when distro-specific spec is missing)
[apps.install_specs.universal]
packages = ["pkg-name"]
```

---

## Categories

Your custom apps can use any category name. Common categories include:

- **Development** — IDEs, compilers, version control
- **Web Browsers** — Firefox, Chrome, etc.
- **Graphics** — Image editors, 3D tools
- **Media** — Video players, music apps
- **Gaming** — Steam, emulators, game launchers
- **Office** — LibreOffice, PDF tools
- **Communication** — Discord, Slack, Telegram
- **Utilities** — File managers, system monitors
- **Security** — Password managers, VPNs, firewalls
- **Custom** — Your own category!

If you create a new category, it will automatically appear in Linite's GUI.

---

## Real-World Examples

### Company VPN Tool

```toml
[[apps]]
id          = "acme-vpn"
name        = "ACME Corp VPN"
description = "Company VPN client for secure remote access"
category    = "Security"
icon        = "🔒"
website     = "https://intranet.acme.com/vpn"
preferred_pm = "apt"

[apps.install_specs.apt]
packages = ["acme-vpn-client"]
pre_commands = [
  "wget -qO- https://packages.acme.com/key.gpg | apt-key add -",
  "echo 'deb https://packages.acme.com/ubuntu focal main' > /etc/apt/sources.list.d/acme-vpn.list",
  "apt-get update"
]
post_commands = [
  "acme-vpn-client config --server vpn.acme.com"
]
```

### Internal Development Tool

```toml
[[apps]]
id          = "internal-cli"
name        = "Internal CLI Tools"
description = "Command-line utilities for project scaffolding"
category    = "Development"
icon        = "🛠️"
website     = "https://github.com/company/internal-cli"

[apps.install_specs.script]
script_url = "https://raw.githubusercontent.com/company/internal-cli/main/install.sh"
```

### Override Built-In Git

```toml
# Use a custom-compiled Git version with specific patches
[[apps]]
id          = "git"
name        = "Git (Custom Build)"
description = "Git with company-specific patches"
category    = "Development"
icon        = "🔧"
website     = "https://git-scm.com"

[apps.install_specs.apt]
packages = ["git-custom"]
pre_commands = [
  "add-apt-repository ppa:company/custom-git",
  "apt-get update"
]
```

---

## Troubleshooting

### My custom apps don't appear

1. **Check the directory path:**
   ```bash
   ls ~/.config/linite/catalog/
   ```
   
2. **Verify TOML syntax:**
   ```bash
   python3 -c "import tomllib; print(tomllib.load(open('~/.config/linite/catalog/my_apps.toml', 'rb')))"
   ```

3. **Check Linite logs:**
   Run Linite with debug logging:
   ```bash
   linite --verbose
   ```
   
   Look for messages about catalog loading.

### App loads but installation fails

- Verify your `install_specs` match the package manager on your system
- Check that `packages` lists are correct for your distro
- Test `pre_commands` manually to ensure they work
- Ensure URLs in `script_url` are accessible

### Duplicate ID warning

If you see:
```
User catalog overrides built-in app: <id>
```

This is **intentional** — your custom definition is replacing the built-in one. If this wasn't intended, change the `id` to something unique.

---

## Sharing Catalogs

### Export for Team Distribution

1. Create a shared repository:
   ```bash
   mkdir company-linite-catalog
   cd company-linite-catalog
   git init
   ```

2. Add your catalog files:
   ```bash
   cp ~/.config/linite/catalog/*.toml .
   git add *.toml
   git commit -m "Company app catalog"
   ```

3. Team members install:
   ```bash
   git clone https://github.com/company/linite-catalog ~/.config/linite/catalog
   ```

### Contributing Upstream

If your custom app would benefit the wider community:

1. Test thoroughly on multiple distros
2. Add the app to the appropriate category file in `data/catalog/`
3. Submit a pull request to the Linite repository

---

## Security Considerations

⚠️ **User catalogs run with sudo privileges during installation**

Best practices:
- ✅ Only load catalogs from trusted sources
- ✅ Always specify `sha256` for script-based installs
- ✅ Review `pre_commands` and `post_commands` before running
- ✅ Use HTTPS URLs for repositories and scripts
- ❌ Never blindly copy untrusted catalog files

---

## FAQ

**Q: Can I disable built-in apps without creating a custom catalog?**  
A: Not directly, but you can override an app with an empty/broken spec so it doesn't install.

**Q: Do user catalogs work in the CLI mode?**  
A: Yes! All CLI commands (`--install`, `--export`, etc.) see user catalogs.

**Q: Can I use categories that don't exist in the built-in catalog?**  
A: Absolutely! Custom categories will appear in the GUI automatically.

**Q: Is there a limit to the number of custom apps?**  
A: No hard limit, but loading 1000+ apps may slow down startup.

**Q: Can I have multiple files defining apps in the same category?**  
A: Yes! Linite merges all `.toml` files, regardless of filename.

---

## See Also

- [Example user catalog](USER_CATALOG_EXAMPLE.toml)
- [Built-in catalog sources](../data/catalog/)
- [Contributing Guide](../CONTRIBUTING.md)
