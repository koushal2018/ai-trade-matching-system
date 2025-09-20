#!/usr/bin/env python3
"""
Release helper script for version management
"""
import re
from datetime import datetime

def prepare_release(version):
    """Prepare changelog for new release"""
    
    # Update CHANGELOG.md
    with open('CHANGELOG.md', 'r') as f:
        content = f.read()
    
    # Replace [Unreleased] with version and date
    today = datetime.now().strftime('%Y-%m-%d')
    new_section = f"## [{version}] - {today}"
    
    # Add new Unreleased section
    unreleased_section = """## [Unreleased]

### Added
- [Add your new features here]

### Changed
- [Add your improvements here]

### Fixed
- [Add your bug fixes here]

"""
    
    content = content.replace("## [Unreleased]", unreleased_section + new_section)
    
    with open('CHANGELOG.md', 'w') as f:
        f.write(content)
    
    # Update VERSION file
    with open('VERSION', 'w') as f:
        f.write(version)
    
    print(f"✅ Prepared release {version}")
    print("📝 Update CHANGELOG.md with your actual changes")
    print("🚀 Ready to commit and tag!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        prepare_release(sys.argv[1])
    else:
        print("Usage: python release_helper.py <version>")
        print("Example: python release_helper.py 0.1.0-alpha.2")