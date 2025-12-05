# Copilot Instructions for obsidian-spaced-repetition-flashcard-generator

## Project Overview
- **Purpose:** Generate high-quality MCQ flashcards from Obsidian lecture notes using local LLMs (Ollama) for the Obsidian Spaced Repetition plugin.
- **Main Entry:** `mcq_flashcards.py` (CLI and dev mode), core logic in `mcq_flashcards/` package.
- **Key Features:**
  - Context-aware MCQ generation (follows `[[wikilinks]]`)
  - Bloom's taxonomy and difficulty targeting
  - Strict output validation and auto-correction
  - Multi-threaded, with JSON-based caching for performance
  - Modular, extensible architecture

## Architecture & Key Components
- `mcq_flashcards/core/`: Configuration, Ollama API client, generation logic
- `mcq_flashcards/processing/`: Output cleaning (`cleaner.py`), validation (`validator.py`)
- `mcq_flashcards/utils/`: Performance tuning, post-processing, system utilities
- `tests/`: 100+ automated tests (unit, integration, robustness)
- Caching, logs, and raw LLM responses in `_cache/`, `_logs/`, `_raw_responses/`

## Developer Workflows
- **Run generator:** `python mcq_flashcards.py` (interactive) or with `-d` for dev mode
- **Test suite:** `pytest` (see README for coverage and options)
- **Dev mode:** Use CLI flags for subject, week, cache management, Bloom's/difficulty, etc.
- **Ollama:** Must be running locally (`ollama serve`)
- **Config:** Centralized in `mcq_flashcards/core/config.py` (env var overrides supported)

## Project-Specific Conventions
- **Output:** Markdown, strict 4-option MCQ format, plugin-compliant
- **Cache:** Only JSON (no pickle), auto-cleared with CLI flags
- **Validation:** All MCQs validated and auto-corrected before output
- **Paths:** Relative to script location; expects `_scripts` at vault root
- **Threading:** Parallel processing for speed, with dynamic tuning

## Integration & Extensibility
- **LLM:** Uses Ollama API (configurable model)
- **Obsidian:** Output targets Spaced Repetition plugin format
- **Environment:** Works cross-platform (Windows/Mac/Linux)

## Examples
- Generate for subject: `python mcq_flashcards.py -d ACCT1001 1`
- Clear cache: `python mcq_flashcards.py -d ACCT1001 1 --clear-cache`
- Custom Bloom's/difficulty: `python mcq_flashcards.py -d ACCT1001 1 --bloom analyze --difficulty hard`

## Testing Conventions
- **Internal Testing:** `pytest` for unit/integration tests (105 tests)
- **Dev Testing:** `python mcq_flashcards.py -d SUBJECT WEEK` (outputs to `tests/_dev/`)
- **Prod Testing:** `python mcq_flashcards.py` (interactive mode, outputs to `Flashcards/`)
- All tests should pass before committing
- Dev mode auto-overwrites files; prod mode prompts for confirmation

## Code Quality Standards
- Use type hints for all function signatures (`from typing import ...`)
- Follow PEP 8 style guide (enforced in future with pre-commit hooks)
- Maximum line length: 100 characters (flexible for readability)
- Use descriptive variable names (no single-letter vars except loop counters)
- Document complex regex patterns with inline comments
- Add docstrings for all public methods (Google style preferred)

## Common Pitfalls to Avoid
- **Security:** Never use `pickle` for caching (use JSON only)
- **Concurrency:** Always use atomic writes for cache files (`tempfile.mkstemp` + `os.replace`)
- **Thread Safety:** Use locks (`self.file_lock`, `self.stats_lock`) for shared resources
- **Validation:** Validate all user inputs before processing (see `Config.validate()`)
- **Logging:** Log errors but avoid log spam in retry loops (log only final failure)
- **Cache Keys:** Include model name in cache key to prevent conflicts

## References
- See `README.md` for full usage, dev, and test instructions
- See `mcq_flashcards/core/config.py` for config patterns
- See `tests/` for test structure and coverage
- See `ARCHITECTURE.md` for design patterns and extension points

## Planned Enhancements (v3.24.x)

**Current Version:** 3.23.0  
**Implementation Status:** Ready to begin  
**Artifacts:** See `.github/task.md` and `.github/enhancement_plan.md`

### Phase 1: Quick Wins
1. **Batch Week Processing** - Process multiple weeks in one command (e.g., `1-4`, `1,3,5`, `ALL`)
2. **Enhanced Progress Indicators** - Show current file/concept being processed with real-time stats
3. **Concept Cache Progress** - Display progress bar when loading 1,000+ concept files

### Phase 2: Performance Optimizations
4. **Smart Cache Invalidation** - Include Bloom's level and difficulty in cache key
5. **Parallel File Reading** - Use ThreadPoolExecutor for faster I/O (2-3x speedup)

### Phase 3: Quality Features
6. **Quality Metrics Report** - Display MCQ quality, concept coverage, and performance metrics after generation
7. **Wikilink Footer (Optional)** - Add "📚 Concepts Covered" section at end of file for graph integration

### Items on Hold (Trade-offs)
- ~~Increase Questions Per Prompt (2→5)~~ - Needs quality testing first
- ~~Reduced LLM Context Size~~ - May reduce quality

### Implementation Protocol
- One feature at a time
- Test with COMM1001 W01 in dev mode
- Run full test suite (125 tests must pass)
- User confirmation required before each commit
- Follow conventional commits (feat/perf/fix)
- Follow SemVer: MINOR for new features, PATCH for improvements (see CONTRIBUTING.md)
- Update version in `__init__.py` and `CHANGELOG.md`

### Important Notes
- **Wikilinks:** Intentionally stripped from MCQ content (SR plugin compatibility)
- **No Trade-offs:** Only implement enhancements without quality/accuracy trade-offs
- **Backward Compatible:** All changes must be backward compatible

---
**For AI agents:**
- Always validate output format and use cache for performance
- Follow project CLI and config conventions
- Reference README and config.py for up-to-date workflows and settings
- Prioritize security (JSON over pickle) and thread safety (use locks)
- Test changes with dev mode before running in production
