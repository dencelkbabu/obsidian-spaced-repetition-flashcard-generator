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
