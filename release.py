#!/usr/bin/env python3
"""
Release management script for AI Trade Matching System
"""
import os
import shutil
import json
from datetime import datetime
from pathlib import Path

def get_current_version():
    """Read current version from VERSION file"""
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.1.0-alpha.1"

def create_release_package(version=None):
    """Create a release package with version tagging"""
    if not version:
        version = get_current_version()
    
    # Create releases directory
    releases_dir = Path("releases")
    releases_dir.mkdir(exist_ok=True)
    
    # Create version-specific directory
    release_dir = releases_dir / f"v{version}"
    if release_dir.exists():
        print(f"Release v{version} already exists!")
        return False
    
    release_dir.mkdir()
    
    # Copy source code
    shutil.copytree("src", release_dir / "src")
    shutil.copytree("data", release_dir / "data", ignore=shutil.ignore_patterns("*.db"))
    
    # Copy essential files
    files_to_copy = [
        "README.md", "requirements.txt", "setup.py", 
        "VERSION", "CHANGELOG.md", ".env.example"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
    
    # Create release metadata
    metadata = {
        "version": version,
        "release_date": datetime.now().isoformat(),
        "type": "pre-release" if "alpha" in version or "beta" in version else "release",
        "files_included": files_to_copy + ["src/", "data/"]
    }
    
    with open(release_dir / "release_info.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Release v{version} created in releases/v{version}/")
    return True

def list_releases():
    """List all available releases"""
    releases_dir = Path("releases")
    if not releases_dir.exists():
        print("No releases found")
        return
    
    releases = sorted([d.name for d in releases_dir.iterdir() if d.is_dir()])
    print("Available releases:")
    for release in releases:
        print(f"  - {release}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_releases()
        elif sys.argv[1] == "create":
            version = sys.argv[2] if len(sys.argv) > 2 else None
            create_release_package(version)
        else:
            print("Usage: python release.py [create|list] [version]")
    else:
        create_release_package()