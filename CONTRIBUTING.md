# Contributing Guidelines

## Commit System
- Follow the **Conventional Commits** specification.
- **Always sign** commits, tags, and releases.
- Keep commit messages **short**.
- Use the **commit message body** for explanations.
- Use **hyphens** for bullet points in the commit body.

## Versioning Strategy

### Major Releases (x.0.0) & Significant Milestones (x.10.0, x.20.0)
- ✅ **Version number in commit message**
- ✅ **Git tag created**
- ✅ Example: `v3.0.0`, `v3.10.0`, `v3.20.0`

### Regular Minor/Patch Releases (x.y.z)
- ✅ **Version number only in code** (`__version__`)
- ❌ **No version in commit message**
- ❌ **No git tag**
- ✅ Example: Current version is `3.21.0` in code, but no tag.

*This keeps the git history clean and tags meaningful!* 🎯

## Semantic Versioning (SemVer) Guidelines

This project follows **Semantic Versioning**: `MAJOR.MINOR.PATCH`

### Version Number Format: `X.Y.Z`

- **MAJOR (X):** Breaking changes, incompatible API changes
- **MINOR (Y):** New features, backward-compatible functionality  
- **PATCH (Z):** Bug fixes, performance improvements, backward-compatible

### When to Bump Each Level

#### MAJOR (X.0.0) - Breaking Changes
- Breaking changes to CLI arguments
- Incompatible changes to output format
- Removal of features
- **Example:** `3.0.0` → `4.0.0`
- **Tagging:** ✅ Always create git tag

#### MINOR (0.Y.0) - New Features
- New CLI arguments or flags (e.g., batch week processing)
- New features (quality reports, wikilink footer)
- New output sections
- New user-facing functionality
- **Example:** `3.23.0` → `3.24.0`
- **Tagging:** ❌ No git tag (unless milestone like x.10.0, x.20.0)

#### PATCH (0.0.Z) - Improvements & Fixes
- Bug fixes
- Performance optimizations (caching, parallel processing)
- UX improvements (progress indicators)
- Internal refactoring
- Documentation updates
- **Example:** `3.24.0` → `3.24.1`
- **Tagging:** ❌ No git tag

### Version Bumping Examples

**New Feature (MINOR):**
```bash
# Add batch week processing
git commit -S -m "feat: add batch week processing support"
# Bump: 3.23.0 → 3.24.0 (in __init__.py only)
```

**Performance Improvement (PATCH):**
```bash
# Optimize file reading
git commit -S -m "perf: parallelize file reading for 2x speedup"
# Bump: 3.24.0 → 3.24.1 (in __init__.py only)
```

**Bug Fix (PATCH):**
```bash
# Fix cache invalidation
git commit -S -m "fix: correct cache key generation for presets"
# Bump: 3.24.1 → 3.24.2 (in __init__.py only)
```

### Version Update Checklist

When bumping version:
1. ✅ Update `mcq_flashcards/__init__.py` (`__version__`)
2. ✅ Update `CHANGELOG.md` with changes
3. ✅ Commit with appropriate conventional commit message
4. ✅ Tag only for MAJOR releases or milestones (x.10.0, x.20.0)

## Changelog Strategy

### Annotated Tags (Major & Milestone Releases)
- Include **full changelog** from previous tagged version.
- List all commits between tags.
- Example: `v3.20.0` tag will contain all commits from `v3.10.0` to `v3.20.0`.

### Benefits
- ✅ Clean git history (no version spam in commit messages).
- ✅ Comprehensive changelogs in tags (auto-generated from commits).
- ✅ Easy to see what changed between major releases.
- ✅ Tags serve as release notes.

## Testing

Before submitting changes, ensure all tests pass:

```bash
# Run the full test suite
pytest

# Run specific tests if needed
pytest tests/test_filename.py
```
