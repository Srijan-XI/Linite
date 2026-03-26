#!/usr/bin/env python3
"""
AppImage Helper Utility

This module provides utilities for working with AppImages in Linite,
including downloading AppImages, verifying checksums, and generating
catalog entries.

Usage:
    python utils/appimage_helper.py --download <app_id> <url>
    python utils/appimage_helper.py --verify <file> <sha256>
    python utils/appimage_helper.py --generate-entry <url>
"""

import argparse
import hashlib
import os
import sys
import urllib.request
from pathlib import Path


def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal SHA-256 checksum
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_appimage(url: str, output_path: str = None) -> str:
    """
    Download an AppImage from a URL.
    
    Args:
        url: URL to the AppImage
        output_path: Where to save the file (defaults to filename from URL)
        
    Returns:
        Path to the downloaded file
    """
    if output_path is None:
        output_path = url.split("/")[-1]
    
    print(f"📥 Downloading AppImage from: {url}")
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"✅ Downloaded to: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Download failed: {e}", file=sys.stderr)
        sys.exit(1)


def verify_sha256(file_path: str, expected_hash: str) -> bool:
    """
    Verify SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        expected_hash: Expected SHA-256 checksum (hex string)
        
    Returns:
        True if checksum matches, False otherwise
    """
    actual_hash = calculate_sha256(file_path)
    if actual_hash.lower() == expected_hash.lower():
        print(f"✅ Checksum verification passed!")
        return True
    else:
        print(f"❌ Checksum mismatch!")
        print(f"   Expected: {expected_hash}")
        print(f"   Actual:   {actual_hash}")
        return False


def generate_catalog_entry(app_id: str, app_name: str, app_url: str, 
                           download_url: str, icon: str = "📦") -> None:
    """
    Generate a TOML catalog entry for an AppImage application.
    
    This downloads the AppImage, calculates its SHA-256, and outputs
    a ready-to-use TOML entry for the catalog.
    
    Args:
        app_id: Application ID (lowercase, no spaces)
        app_name: Display name of the application
        app_url: Website URL of the application
        download_url: Direct download URL for the AppImage
        icon: Emoji icon for the application
    """
    # Download the AppImage temporarily
    print(f"🔍 Generating catalog entry for: {app_name}")
    print()
    
    temp_file = f"/tmp/{app_id}.AppImage"
    download_appimage(download_url, temp_file)
    
    # Calculate SHA-256
    print(f"📊 Calculating SHA-256 checksum...")
    sha256_hash = calculate_sha256(temp_file)
    print(f"✅ SHA-256: {sha256_hash}")
    print()
    
    # Extract binary name from download URL
    binary_name = app_name.replace(" ", "")
    
    # Generate TOML entry
    print("📝 TOML catalog entry:")
    print("=" * 70)
    toml_entry = f"""[[apps]]
id          = "{app_id}"
name        = "{app_name}"
description = "[Add a brief description here]"
category    = "[Add category here]"
icon        = "{icon}"
website     = "{app_url}"
preferred_pm = "flatpak"  # Set to your preferred PM, or remove if AppImage only

# Optional: Add Flatpak spec if available
# [apps.install_specs.flatpak]
# packages = ["com.example.{app_name}"]

# AppImage installation spec
[apps.install_specs.appimage]
packages = ["{binary_name}"]
script_url = "{download_url}"
sha256 = "{sha256_hash}"
"""
    print(toml_entry)
    print("=" * 70)
    print()
    
    # Cleanup
    if Path(temp_file).exists():
        os.remove(temp_file)
        print("🧹 Cleaned up temporary AppImage file")


def main():
    parser = argparse.ArgumentParser(
        description="AppImage helper for Linite catalog management"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Download command
    download_parser = subparsers.add_parser(
        "download", help="Download an AppImage from a URL"
    )
    download_parser.add_argument("url", help="URL to the AppImage")
    download_parser.add_argument(
        "-o", "--output", help="Output file path", default=None
    )
    
    # Verify command
    verify_parser = subparsers.add_parser(
        "verify", help="Verify SHA-256 checksum of an AppImage"
    )
    verify_parser.add_argument("file", help="Path to the AppImage file")
    verify_parser.add_argument("sha256", help="Expected SHA-256 checksum")
    
    # Generate entry command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate a catalog entry for an AppImage"
    )
    generate_parser.add_argument("app_id", help="Application ID (e.g., obsidian)")
    generate_parser.add_argument("app_name", help="Application name (e.g., Obsidian)")
    generate_parser.add_argument("app_url", help="Application website URL")
    generate_parser.add_argument("download_url", help="Direct AppImage download URL")
    generate_parser.add_argument(
        "-i", "--icon", help="Emoji icon", default="📦"
    )
    
    args = parser.parse_args()
    
    if args.command == "download":
        download_appimage(args.url, args.output)
    elif args.command == "verify":
        if verify_sha256(args.file, args.sha256):
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.command == "generate":
        generate_catalog_entry(
            args.app_id, args.app_name, args.app_url,
            args.download_url, args.icon
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
