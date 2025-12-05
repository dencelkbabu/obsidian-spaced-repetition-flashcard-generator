# Contributing Guidelines

## Commit Message Format

### Structure
```
<type>: <subject>

<body>

bumped version to x.y.z
```

### Rules
1. **Follow Conventional Commits** specification
2. **Always sign commits** (`git commit -S`)
3. **Subject line**: Short, lowercase, no period
4. **Body**: Lowercase, use hyphens for bullets, blank line after subject
5. **Version**: Last line, format: "bumped version to x.y.z"

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding or updating tests
- `perf`: Performance improvement
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `chore`: Maintenance tasks

## Commit Message Template

```
<type>: <short description (lowercase, no period)>

- <change 1 (lowercase, starts with verb)>
- <change 2>
- <change 3>

<optional context paragraph (lowercase)>

<optional examples section>

bumped version to x.y.z
```

## Real Examples

### Example 1: Feature Addition
```
feat: add batch week processing support

- add parse_week_argument() helper for week range/list parsing
- support week ranges (1-4), comma-separated (1,3,5), and mixed (1-3,5)
- modify execute_generation() to accept list of weeks
- update CLI help text with new week format examples
- add 11 comprehensive test cases

fully backward compatible with existing single week/ALL syntax
examples:
  python cli.py -d COMM1001 1-4      # Weeks 1-4
  python cli.py -d COMM1001 1,3,5    # Weeks 1,3,5
  python cli.py -d COMM1001 1-3,5,7  # Mixed

tests: 136 passed (125 original + 11 new)

bumped version to 3.24.0
```

### Example 2: Bug Fix
```
fix: correct type hint from 'any' to 'Any'

- added 'Any' to typing imports in generator.py
- changed lowercase 'any' to proper 'Any' in _save_raw_log method signature
- improves type safety and IDE support

bumped version to 3.22.2
```

### Example 3: Test Addition
```
test: comprehensive test suite improvements

- fixed outdated model reference (llama3:8b → llama3.1:8b)
- fixed outdated cache format (.pkl → .json)
- added 17 new tests across 3 files:
  * test_prompts.py (12 tests) - prompt template validation
  * test_self_correction.py (3 tests) - stats tracking
  * test_concept_caching.py (2 tests) - v3.18.0 feature
- enhanced config validation tests (9 test cases)
- updated README.md test count (105 → 125)
- updated README.md model reference
- all 125 tests passing

bumped version to 3.23.0
```

### Example 4: Documentation
```
docs: add AI agent documentation and SemVer guidelines

- add comprehensive copilot instructions for AI agents
- add enhancement plan (7 features planned for v3.24-3.26)
- add implementation task checklist with SemVer versioning
- add detailed SemVer guidelines to CONTRIBUTING.md
- track .github/ folder in git (removed from .gitignore)

bumped version to 3.23.1
```

## Formatting Rules

### DO ✅
- Use lowercase for everything (subject, body, examples)
- Start bullet points with verbs (add, fix, update, remove)
- Use hyphens (`-`) for bullet points
- Use asterisks (`*`) for sub-bullets
- Keep subject line under 50 characters
- Add blank line between subject and body
- Put version bump as last line
- Use present tense ("add" not "added")

### DON'T ❌
- Don't capitalize (except proper nouns like "Bloom's", "CLI")
- Don't use periods at end of subject line
- Don't use "Version:" prefix (just "bumped version to")
- Don't put version in subject line (only in body)
- Don't use past tense in bullet points

## Versioning Strategy

### Major Releases (x.0.0) & Significant Milestones (x.10.0, x.20.0)
- ✅ **Version number in commit message**
- ✅ **Git tag created**
- ✅ **CHANGELOG.md updated**
- ✅ Example: `v3.0.0`, `v3.10.0`, `v3.20.0`

### Regular Minor/Patch Releases (x.y.z)
- ✅ **Version number only in code** (`__version__`)
- ✅ **Version in commit body** ("bumped version to x.y.z")
- ❌ **No version in commit subject**
- ❌ **No git tag**
- ❌ **No CHANGELOG.md update** (only at milestones)
- ✅ Example: Current version is `3.25.0` in code, but no tag

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
