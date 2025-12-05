# Changelog

All notable changes to the Obsidian Spaced Repetition Flashcard Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
