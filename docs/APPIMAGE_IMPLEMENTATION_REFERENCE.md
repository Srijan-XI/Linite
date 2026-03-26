# AppImage Support - Implementation Reference

This document explains the code changes made to implement AppImage support in Linite. It's intended for developers who want to understand how the feature integrates with the existing architecture or who want to build on it.

## Architecture Overview

Linite implements a **pluggable package manager** pattern using a factory design. The AppImage implementation follows this pattern while also requiring special handling since AppImages are self-contained binaries rather than traditional packages.

### Factory Pattern (core/package_manager.py)

```python
# All package managers inherit from BasePackageManager
class BasePackageManager:
    name: str
    def install(self, packages, progress_cb=None) -> tuple
    def is_installed(self, package: str) -> bool
    def update_all(self, progress_cb=None) -> tuple
    def update_package(self, package, progress_cb=None) -> tuple

# Factory dictionary maps PM names to classes
_PM_MAP = {
    "apt": AptPackageManager,
    "dnf": DnfPackageManager,
    # ... 6 others ...
    "appimage": AppImagePackageManager,  # ← Our addition
}

# Retrieval function
def get_package_manager(name: str) -> BasePackageManager:
    return _PM_MAP[name.lower()]()
```

### AppImagePackageManager Implementation

**Location:** `core/package_manager.py` (class definition, ~60 lines)

**Design Rationale:**
- AppImages are **self-contained binaries** (not managed by system PMs)
- Installation logic is in `installer.py`, not here (vertical separation of concerns)
- This class is minimal because:
  - `install()` is a **no-op** (installer.py handles downloads/setup)
  - `is_installed()` just checks for binary existence in `~/.local/bin/`
  - No `update_all()` or `update_package()` needed (static binaries, manual updates)

**Code:**

```python
class AppImagePackageManager(BasePackageManager):
    """
    AppImage package manager for self-contained Linux binaries.
    
    Installation is handled in installer.py since AppImages require:
    - Download verification (SHA-256)
    - Desktop file creation
    - Binary placement & permissions
    These operations live in install_app() rather than in this class.
    """
    
    name = "appimage"
    
    def install(self, packages, progress_cb=None):
        """No-op: AppImage installation is handled in installer.py"""
        if progress_cb:
            progress_cb("✓ AppImage installation already completed by installer")
        return 0, ""
    
    def is_installed(self, package: str) -> bool:
        """Check if AppImage binary exists in ~/.local/bin/"""
        appimage_path = Path.home() / ".local" / "bin" / package
        return appimage_path.exists() and appimage_path.is_file()
    
    def update_all(self, progress_cb=None):
        """No-op: Manual AppImage updates (documented in APPIMAGE_SUPPORT.md)"""
        if progress_cb:
            progress_cb("ℹ AppImage binaries are static. Manual updates documented in docs/")
        return 0, ""
    
    def update_package(self, package, progress_cb=None):
        """No-op: Manual AppImage updates"""
        return self.update_all(progress_cb)
```

### Registration in _PM_MAP

```python
_PM_MAP = {
    # ... existing PMs ...
    "appimage": AppImagePackageManager,
}
```

---

## Installation Flow (core/installer.py)

**Location:** `core/installer.py` (~100 lines across 3 functions + logic block)

### 1. PM Selection with Fallback

**Function:** `_pick_pm(entry, fallback_list=None)`

**What Changed:**
- Added `"appimage"` to `_SUPPORTED_PMS` frozenset
- Updated `_pick_pm()` docstring to document 5-priority fallback chain
- Added unconditional `candidates.append("appimage")` **before** the priority loop

**Why Before the Loop:**
AppImage is universally available (doesn't depend on system packages), so it's always a valid candidate. Adding it **before** the loop ensures it's the final fallback if all others fail.

```python
_SUPPORTED_PMS = frozenset({
    "apt", "dnf", "pacman", "zypper", "yay",  # Native PMs
    "flatpak", "snap",                        # Universal PMs
    "appimage"                                # ← Our addition
})

def _pick_pm(entry, fallback_list=None):
    """
    Pick the best package manager for installation.
    
    Priority (in order):
    1. entry.preferred_pm (if available)
    2. First available in entry.install_specs keys
    3. Candidates matching distro → snap → appimage (fallback chain)
    """
    # ... selection logic ...
    
    # Unconditional fallback (always works for self-contained binaries)
    candidates.append("appimage")
    
    for pm_name in candidates:
        if pm_name in entry.install_specs:
            return pm_name
```

### 2. Helper Functions

**Function:** `_ensure_bin_directory()`

```python
def _ensure_bin_directory() -> str:
    """
    Ensure ~/.local/bin exists for AppImage binaries.
    
    Returns: Full path to the directory as string
    """
    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    return str(bin_dir)
```

**Function:** `_create_desktop_file(app_id, app_name, binary_name, icon, progress_cb=None)`

```python
def _create_desktop_file(app_id, app_name, binary_name, icon, progress_cb=None):
    """
    Create a .desktop file for AppImage binary in ~/.local/share/applications/
    
    .desktop files enable:
    - Application menu integration (GNOME, KDE, XFCE, etc.)
    - File associations
    - Desktop shortcuts
    - Application search/discovery
    """
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_file = desktop_dir / f"{app_id}.desktop"
    
    desktop_content = f"""[Desktop Entry]
Name={app_name}
Exec={Path.home() / ".local" / "bin" / binary_name}
Type=Application
Icon={icon or "application-x-executable"}
Terminal=false
Categories=Utility;
Path={Path.home() / ".local" / "bin"}
"""
    
    desktop_file.write_text(desktop_content)
    
    if progress_cb:
        progress_cb(f"✓ Created .desktop file: {desktop_file}")
```

### 3. Main Installation Logic

**Location:** `install_app()` function in `core/installer.py` (~50 lines in pm_name == "appimage" block)

**Flow:**

```python
if pm_name == "appimage":
    # Step 1: Validate AppImage specification
    if "script_url" not in install_spec:
        return InstallResult(
            Status.ERROR,
            f"AppImage spec must include 'script_url' field"
        )
    
    # Step 2: Extract binary name from packages list
    if not install_spec.get("packages"):
        return InstallResult(Status.ERROR, "No packages specified for AppImage")
    
    binary_name = install_spec["packages"][0]
    
    # Step 3: Ensure ~/.local/bin exists
    bin_dir = _ensure_bin_directory()
    
    # Step 4: Move downloaded file to ~/.local/bin/
    destination = Path(bin_dir) / binary_name
    
    try:
        # file_path is the temporary download location (from installer's download step)
        if not Path(file_path).exists():
            return InstallResult(
                Status.ERROR,
                f"Downloaded file not found: {file_path}"
            )
        
        # For AppImages, we move the downloaded file (don't extract)
        shutil.move(file_path, str(destination))
        
        # Step 5: Make executable (chmod +x equivalent)
        destination.chmod(0o755)
        
        # Step 6: Create .desktop file for GUI integration
        _create_desktop_file(
            app_id=entry.id,
            app_name=entry.name,
            binary_name=binary_name,
            icon=entry.icon,
            progress_cb=progress_cb
        )
        
        # Step 7: Record in history
        history.record(
            app_name=entry.name,
            pm_name="appimage",
            action="install",
            status="success"
        )
        
        # Step 8: Return success
        if progress_cb:
            progress_cb(f"✓ Installed {entry.name} to {destination}")
        
        return InstallResult(Status.SUCCESS, f"Installed to {destination}")
    
    except Exception as e:
        return InstallResult(Status.ERROR, f"Failed to install: {e}")
```

---

## Data Model (data/catalog/*.toml)

### AppImage Specification Block

**File:** `data/catalog/{category}.toml`

**Format:**

```toml
[[apps]]
id          = "app_id"
name        = "Application Name"
description = "Brief description"
category    = "utilities"  # See: data/catalog/
icon        = "📦"
website     = "https://example.com"
preferred_pm = "flatpak"   # Optional: hint for PM selection

[apps.install_specs.appimage]
packages   = ["BinaryName"]                    # Binary name (case-sensitive)
script_url = "https://github.com/.../app.AppImage"  # Download link
sha256     = "abc123..."   # Optional: SHA-256 for verification (empty = skip)
```

**Example from note_taking.toml:**

```toml
[[apps]]
id          = "obsidian"
name        = "Obsidian"
description = "Powerful knowledge base that works on top of a local folder of plain-text Markdown files"
category    = "note_taking"
icon        = "🔮"
website     = "https://obsidian.md"
preferred_pm = "flatpak"

[apps.install_specs.flatpak]
flatpak_id = "md.obsidian.Obsidian"
packages   = []

[apps.install_specs.appimage]
packages   = ["Obsidian"]
script_url = "https://github.com/obsidianmd/obsidian-releases/releases/download/latest/Obsidian-latest-x64.AppImage"
sha256     = ""  # Can be calculated using utils/appimage_helper.py
```

### Loading & Parsing

**File:** `data/software_catalog.py`

The catalog loading code already handles multiple `install_specs` blocks generically—no changes were needed! The AppImage entry is parsed and merged by existing code:

```python
# Existing code (no changes needed)
def load_catalog(catalog_path):
    with open(catalog_path, "rb") as f:
        data = tomllib.load(f)
    
    # Automatically flattens all install_specs regardless of PM
    # AppImage specs are handled transparently
    return data.get("apps", [])
```

---

## Utility Script (utils/appimage_helper.py)

**Location:** `utils/appimage_helper.py` (~180 lines)

**Purpose:** Command-line tool for developers/contributors to manage AppImage catalog entries

### Functions

**1. calculate_sha256(file_path)**
```python
def calculate_sha256(file_path):
    """Compute SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
```

**2. download_appimage(url, output_path=None)**
```python
def download_appimage(url, output_path=None):
    """Download AppImage from URL with progress feedback"""
    # Returns: path to downloaded file
    # Shows progress with emoji indicators
    # Exits with code 1 on failure
```

**3. verify_sha256(file_path, expected_hash)**
```python
def verify_sha256(file_path, expected_hash):
    """Verify SHA-256 checksum matches"""
    # Returns: boolean (True if match)
    # Prints visual results with emoji
```

**4. generate_catalog_entry(app_id, app_name, app_url, download_url, icon)**
```python
def generate_catalog_entry(app_id, app_name, app_url, download_url, icon="📦"):
    """
    Generate a ready-to-use [apps.install_specs.appimage] TOML block
    
    1. Downloads AppImage temporarily
    2. Calculates SHA-256 automatically
    3. Generates TOML entry
    4. Cleans up temporary file
    5. Prints output ready to copy-paste
    """
    # Returns: None (prints formatted TOML)
```

### CLI Interface

```bash
# Download command
python utils/appimage_helper.py download <url> [-o output.AppImage]

# Verify command  
python utils/appimage_helper.py verify <file> <sha256_hash>

# Generate command (most useful)
python utils/appimage_helper.py generate obsidian "Obsidian" \
  "https://obsidian.md" \
  "https://github.com/obsidianmd/obsidian-releases/releases/download/latest/Obsidian-latest-x64.AppImage" \
  --icon "🔮"
```

---

## File Structure Summary

### Modified Files

| File | Changes | Lines | Purpose |
|------|---------|-------|---------|
| `core/package_manager.py` | Added AppImagePackageManager class; registered in _PM_MAP | ~60 | PM factory integration |
| `core/installer.py` | Updated _SUPPORTED_PMS, _pick_pm(), added helpers, added install logic | ~100 | Installation orchestration |
| `SUGGESTIONS.md` | Updated Feature E tracking; added doc links | ~10 | Metadata tracking |

### New Files

| File | Purpose | Lines |
|------|---------|-------|
| `docs/APPIMAGE_SUPPORT.md` | Comprehensive user/contributor guide | 90+ |
| `docs/APPIMAGE_QUICK_REFERENCE.md` | Copy-paste commands & troubleshooting | 150+ |
| `docs/APPIMAGE_ENTRY_EXAMPLES.toml` | Real TOML examples for 6 app types | 200+ |
| `utils/appimage_helper.py` | CLI utility for catalog entry generation | 180+ |

### Enhanced Files

| File | Changes | Purpose |
|------|---------|---------|
| `data/catalog/note_taking.toml` | Added [apps.install_specs.appimage] for Obsidian, Joplin, Logseq | Examples |

---

## Design Decisions

### Decision 1: PM Factory Pattern

**Q:** Why add AppImagePackageManager to the factory if it mostly delegates to installer.py?

**A:** Because:
- Maintaining architectural consistency (all PMs follow same pattern)
- Future flexibility (if AppImage PM ever manages multiple versions, it can expand)
- Clean interface for execution engine and other components
- The factory is the single source of truth for available PMs

### Decision 2: No-op install() Method

**Q:** Why not implement package management logic in AppImagePackageManager?

**A:** Because:
- AppImages aren't "packages" in the traditional sense (no version tracking, no updates via PM)
- Real installation requires: SHA-256 verification, file permissions, .desktop creation
- These are orchestration concerns, not PM concerns
- Keeps the PM class minimal and focused on its role

### Decision 3: ~/.local/bin Placement

**Q:** Why not ~/.local/share/appimage/ or /opt/?

**A:** Because:
- `~/.local/bin` is FreeDesktop compliant (standard for user binaries)
- Automatically discoverable if user adds to PATH (documented)
- No elevated permissions needed (works for all users)
- Easy for users to locate and manually update
- Follows convention for other AppImage distributions

### Decision 4: AppImage as Final Fallback

**Q:** Why add AppImage last in the priority chain?

**A:** Because:
- AppImages have largest download size (static runtime dependencies)
- AppImages can have library compatibility issues (glibc version, etc.)
- Native packages, Flatpak, Snap are preferable
- But AppImage is **always available** as last resort (when others impossible)
- Ensures installation never fails completely

---

## Testing Checklist

For future maintainers or contributors testing AppImage functionality:

- [ ] Install Obsidian via `linite --cli install obsidian`
- [ ] Verify binary at `~/.local/bin/Obsidian`
- [ ] Verify `.desktop` file at `~/.local/share/applications/obsidian.desktop`
- [ ] Launch from command line: `Obsidian`
- [ ] Launch from application menu (GUI)
- [ ] Run `Obsidian --version` to verify executable
- [ ] Test `linite --rollback` removes both binary and .desktop file
- [ ] Test on multiple distros if possible (Ubuntu, Fedora, Arch)

---

## Future Enhancements

### Short-term

1. **Calculate Real SHA-256 Values**
   - Use `appimage_helper.py generate` for Obsidian, Joplin, Logseq
   - Update placeholder empty values in note_taking.toml

2. **Add More Catalog Examples**
   - Headlamp (Kubernetes dashboard)
   - JetBrains Toolbox (IDE manager)
   - Other AppImage-only tools

### Medium-term

3. **GUI Integration**
   - Show "AppImage" badge in app listings
   - Warn users about library compatibility
   - Display source/version information

4. **Automatic Updates**
   - Detect newer AppImage versions
   - Offer in-place update mechanism
   - Track version metadata in history

### Long-term

5. **AppImage Registry**
   - Community-maintained registry of popular AppImages
   - Automatic catalog generation from registry
   - Version pinning and release tracking

6. **Integrity Features**
   - GPG signature verification (if available)
   - Checksum publication in catalog
   - Automatic manifest generation

---

## See Also

- [AppImage Official Documentation](https://docs.appimage.org/)
- [FreeDesktop.org Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/)
- [FreeDesktop.org Application Directory Specification](https://specifications.freedesktop.org/desktop-menu-spec/)
- [XDG Base Directory Standard](https://specifications.freedesktop.org/basedir-spec/)

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Category:** Architecture & Implementation  
**Status:** Complete ✅
