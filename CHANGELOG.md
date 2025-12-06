# Changelog

All notable changes to the Obsidian Spaced Repetition Flashcard Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.30.0] - 2025-12-06

### Summary
MCQ volume reduction for better study manageability. Reduced from 5 to 3 MCQs per file.

### Changed
- Reduced `QUESTIONS_PER_PROMPT` from 5 to 3
- Total MCQs: 930 → 558 (40% reduction)
- Study time: 15 hours → 9 hours

### Performance
- ~5% faster generation (less LLM processing)
- More manageable study volume

## [3.29.0] - 2025-12-05

### Added
- Comprehensive logging system with DEBUG support
- Timestamped log files (`flashcard_gen_YYYYMMDD_HHMM.log`)
- `--debug` CLI flag for verbose logging
- Environment variable support (`FLASHCARD_DEBUG`)
- Detailed logging for:
  - Cache operations (hits/misses)
  - API calls (timing, token counts)
  - File processing (characters, concepts)
  - Worker activity tracking

## [3.28.0] - 2025-12-05

### Added
- Parallel file reading for faster I/O
- ThreadPoolExecutor for concurrent file operations
- Improved startup time for large batches

### Performance
- Faster initial file processing
- Maintains deterministic file order

## [3.27.0] - 2025-12-04

### Added
- Smart cache invalidation for preset-based caching
- Preset-based cache keys (bloom level + difficulty)
- Automatic cache invalidation on preset change

### Fixed
- Prevents stale cached MCQs when changing presets
- No manual cache clearing needed

## [3.26.0] - 2025-12-03

### Added
- Enhanced progress indicators with real-time stats
- Cache hit rate display
- Questions per minute (QPM) tracking
- Batch progress for multiple subjects
- Live progress bars with tqdm

### Changed
- Improved visibility into generation process
- Better completion statistics

## [3.25.0] - 2025-12-02

### Performance
- **2.6x faster generation** - Major performance breakthrough
- Increased `QUESTIONS_PER_PROMPT` from 2 to 5
- Reduced API calls by 80%

### Changed
- Generate 5 MCQs per API call instead of 1
- Same quality, significantly better efficiency

### Benchmark
```
Before: 5 API calls for 5 MCQs
After:  1 API call for 5 MCQs
Speedup: 2.6x
```

## [3.24.0] - 2025-11-28

### Added
- Batch week processing support
- Week ranges: `1-4`
- Comma-separated weeks: `1,3,5`
- Mixed format: `1-3,5,7-9`
- `parse_week_argument()` helper function

### Changed
- Modified `execute_generation()` to accept week lists
- Updated CLI help text with examples

### Examples
```bash
python cli.py -d COMM1001 1-4      # Weeks 1-4
python cli.py -d COMM1001 1,3,5    # Weeks 1,3,5
python cli.py -d COMM1001 1-3,5    # Mixed
```

## [3.23.0] - 2025-11-25

### Added
- Comprehensive commit guidelines and template
- `.github/commit_template.txt`
- Commit message format standards
- Semantic versioning rules

### Documentation
- Subject: lowercase, no period, <50 chars
- Body: lowercase, use hyphens for bullets
- Version: last line format

## [3.22.0] - 2025-11-20

### Added
- Universal benchmark script for v2.6+
- Performance comparison across versions
- GPU utilization tracking
- Questions per minute (QPM) metrics

### Usage
```bash
python benchmark.py --subject COMM1001 --week 1
```

## [3.21.0] - 2025-11-18

### Added
- Comprehensive test suite improvements
- Edge case testing
- Concurrency tests
- Bloom's level and difficulty validation tests

### Changed
- Expanded test coverage
- Improved test organization

## [3.20.0] - 2025-12-05

### Summary
Comprehensive code quality improvements based on fresh code review. Enhanced reliability, performance, and maintainability across 9 recommendations.

### Added
- Progress bar for cache clearing operations using tqdm (v3.19.0)
- Concept file name caching for improved performance (v3.18.0)
- Environment variable support for `VAULT_ROOT` path configuration (v3.17.0)
- Atomic cache writes to prevent race conditions (v3.16.0)
- Logging for cache read failures (v3.15.2)
- Performance metrics tracking (duration, throughput) (v3.14.0)
- Input validation for paths, week ranges, and worker counts (v3.13.0)
- Robust logging with `RotatingFileHandler` (v3.12.0)

### Changed
- Migrated cache from `pickle` to `JSON` for security (v3.15.0)
- Standardized all tests to `pytest` style (v3.14.1)
- Refactored preset selection to use loop (v3.18.1)

### Fixed
- Silent cache failures now logged (v3.15.2)
- CLI cache clearing now handles JSON files (v3.15.1)
- Added missing return type hints (v3.16.1)
- Race conditions in concurrent cache writes (v3.16.0)

### Security
- Eliminated arbitrary code execution risk by replacing `pickle` with `JSON` (v3.15.0)

## [3.19.0] - 2025-12-05

### Added
- Progress bar for cache clearing using tqdm
- Improves UX for large cache operations

## [3.18.1] - 2025-12-05

### Changed
- Refactored preset selection display to use loop
- Eliminates code duplication in CLI

## [3.18.0] - 2025-12-05

### Added
- Concept file name caching for performance
- Pre-loads concept file names at initialization
- Reduces file I/O during wikilink extraction

## [3.17.0] - 2025-12-05

### Added
- Environment variable support for paths
- `VAULT_ROOT` can now be overridden via environment variable
- Prevents breakage when script is moved

## [3.16.1] - 2025-12-05

### Fixed
- Added missing return type hints (`-> None`) to helper methods
- Improves type safety and IDE support

## [3.16.0] - 2025-12-05

### Added
- Atomic cache writes using `tempfile.mkstemp()` and `os.replace()`
- Prevents race conditions during concurrent cache writes

## [3.15.2] - 2025-12-05

### Fixed
- Added logging for cache read failures
- Logs cache corruption errors instead of silently ignoring
- Improves debuggability

## [3.15.1] - 2025-12-05

### Fixed
- Updated CLI to clear JSON cache files
- Ensures `--deep-clear` works with new JSON cache format
- Clears both `.json` and `.pkl` files

## [3.15.0] - 2025-12-05

### Changed
- Migrated cache from `pickle` to `JSON`
- Eliminates security risk of arbitrary code execution
- Cache files are now human-readable

### Security
- Removed `pickle` deserialization vulnerability

## [3.14.1] - 2025-12-05

### Changed
- Standardized tests to `pytest` style
- Converted `test_logging.py` and `test_config.py` to pytest fixtures
- Removed `unittest` boilerplate

## [3.14.0] - 2025-12-05

### Added
- Performance metrics tracking
- Tracks duration and throughput (questions/minute)
- Displays metrics in final report

## [3.13.0] - 2025-12-05

### Added
- Input validation for configuration
- Validates semester paths, week ranges, and worker counts
- Prevents runtime errors with early validation

## [3.12.0] - 2025-12-05

### Added
- Robust logging with `RotatingFileHandler`
- Logs to `_logs/flashcard_gen.log` with 5MB rotation
- Proper error logging for retry failures

## [3.11.0] - 2025-12-05

### Changed
- Extracted prompt templates to separate module (`mcq_flashcards/core/prompts.py`)
- Improves maintainability and configurability

### Added
- 6 missing tests (total: 87 tests)

## [3.10.0] - 2025-12-05

### Added
- Stricter MCQ validation
  - Validates exactly 4 options
  - Validates answer number (1-4)
  - Requires explanation to be present
- 6 new test cases (total: 83 tests)

### Changed
- Improved MCQ validator with comprehensive checks

## [3.9.2] - 2025-12-05

### Added
- Comprehensive automated testing infrastructure (83 tests total)
- Unit tests for MCQCleaner, AutoTuner, MCQValidator
- Integration tests for OllamaClient, Generator, CLI
- Test fixtures and pytest configuration

## [3.0.0 - 3.9.1] - 2025-12-04

### Changed
- **BREAKING:** Modularized flashcard generator into package structure
- Refactored into `mcq_flashcards/` package with `core/`, `processing/`, `utils/` modules

### Added
- Automatic post-processing with verification
- Preset system for study modes (Exam Prep, Quick Review, Deep Study, Mixed)
- Difficulty levels for MCQ generation
- Bloom's Taxonomy targeting
- Dev/prod modes and cache clearing
- Semester selection with interactive prompt
- Auto-cleanup of `_dev` folder in prod mode

### Fixed
- Escaped newlines and regex patterns
- Output quality with automatic cleanup

## [2.7.0] - Previous

### Added
- Modular package structure
- Post-processor for output quality
- Interactive UX improvements

## [2.6.0] - Previous

### Added
- Batch processing for multiple subjects
- Improved error handling

## [2.0.0] - Previous

### Added
- AutoTuner for dynamic performance optimization
- Self-correction mechanism for invalid outputs
