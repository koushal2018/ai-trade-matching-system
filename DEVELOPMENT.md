# Development Workflow

## Working on New Release (v0.1.0-alpha.2)

### Current Status
- **Current Release**: v0.1.0-alpha.1 (stable)
- **Next Release**: v0.1.0-alpha.2 (in development)
- **Branch**: develop

### Development Process

1. **Make Changes**
   ```bash
   # Work on your enhancements
   # Edit files, add features, fix bugs
   ```

2. **Track Changes**
   - Update `CHANGELOG.md` under `[Unreleased]` section
   - Add features under `### Added`
   - Add improvements under `### Changed`
   - Add fixes under `### Fixed`

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: your enhancement description"
   ```

4. **Ready for Release**
   ```bash
   # Update changelog
   python release.py prepare 0.1.0-alpha.2
   
   # Create release
   git add .
   git commit -m "release: v0.1.0-alpha.2"
   git tag -a v0.1.0-alpha.2 -m "Release v0.1.0-alpha.2"
   
   # Push to GitHub
   git push origin develop
   git push origin v0.1.0-alpha.2
   ```

### Version Strategy
- **Alpha**: `0.1.0-alpha.1`, `0.1.0-alpha.2` (pre-release)
- **Beta**: `0.1.0-beta.1` (feature complete)
- **Release**: `0.1.0` (stable)
- **Patch**: `0.1.1` (bug fixes)

### Branch Strategy
- **main**: Stable releases only
- **develop**: Active development
- **feature/xxx**: Individual features (optional)