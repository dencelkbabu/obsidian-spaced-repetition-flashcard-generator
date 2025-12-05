# 🧠 Obsidian Spaced Repetition Flashcard Generator

**Turn your lecture notes into active recall tools instantly.**

This Python tool leverages local LLMs (via Ollama) to analyze your Obsidian vault, understand your lecture notes and linked concepts, and generate high-quality Multiple Choice Questions (MCQs). The output is perfectly formatted for the **[Obsidian Spaced Repetition](https://github.com/st3v3nmw/obsidian-spaced-repetition/)** plugin, allowing you to seamlessly integrate them into your study workflow.

🔗 **Repository:** [https://github.com/dencelkbabu/obsidian-spaced-repetition-flashcard-generator](https://github.com/dencelkbabu/obsidian-spaced-repetition-flashcard-generator)

## ✨ Key Features

*   **🤖 AI-Powered:** Uses Llama 3 (or any Ollama model) to generate grounded, accurate questions.
*   **⚡ High Performance:** Multi-threaded processing and smart caching ensure fast subsequent runs.
*   **🔗 Context-Aware:** Intelligently scans your lecture notes and follows `[[wikilinks]]` to generate concept-specific cards.
*   **🛠️ Robust & Portable:** Features automatic retries, error handling, and works on any OS (Windows/Mac/Linux) with relative path configuration.
*   **📝 Obsidian Ready:** Outputs clean Markdown formatted strictly for the Spaced Repetition plugin.
*   **🚀 AutoTuner (v2.0):** Dynamically monitors your GPU (Nvidia) and error rates to optimize performance and prevent overheating.
*   **🔄 Self-Correction (v2.0):** Automatically detects invalid outputs and prompts the AI to fix them, ensuring high success rates.
*   **🧹 Auto-Cleanup (v2.7):** Post-processor automatically fixes LLM output inconsistencies and verifies quality.
*   **📦 Modular Architecture (v2.7):** Clean package structure for better maintainability and extensibility.
*   **🧪 Comprehensive Testing (v3.20.0):** 101 automated tests ensure code quality and reliability.
*   **✅ Strict Validation (v3.10.0):** Enhanced validator catches malformed MCQs earlier.
*   **🔒 Secure Caching (v3.15.0):** JSON-based cache eliminates security risks of pickle serialization.
*   **📊 Performance Metrics (v3.14.0):** Track generation speed and throughput.
*   **🎯 Bloom's Taxonomy (v3.11.0):** Target specific cognitive levels for your study needs.
*   **⚙️ Configurable Paths (v3.17.0):** Environment variable support for flexible deployment.

## 🚀 Prerequisites

1.  **[Obsidian Spaced Repetition Plugin](https://github.com/st3v3nmw/obsidian-spaced-repetition/)**: Required for reviewing the flashcards.
2.  **Ollama**: Installed and running locally.
    *   Default Model: `llama3:8b` (Configurable).
3.  **Python 3.8+**: With the following dependencies:
```bash
pip install requests pyyaml tqdm pytest
```

## 📂 Project Structure

```text
_scripts/
├── mcq_flashcards.py          # Backwards-compatible entry point
├── cli.py                     # Main CLI interface
├── pytest.ini                 # Test configuration
├── tests/                     # Test suite (101 tests)
└── mcq_flashcards/            # Core package
    ├── core/                  # Core functionality
    │   ├── config.py          # Configuration & constants
    │   ├── client.py          # Ollama API client
    │   └── generator.py       # Main generation logic
    ├── processing/            # Text processing
    │   ├── cleaner.py         # Output cleaning
    │   └── validator.py       # Format validation
    └── utils/                 # Utilities
        ├── autotuner.py       # Dynamic performance tuning
        ├── power.py           # System power management
        └── postprocessor.py   # Output post-processing
```

## 📂 Vault Structure

The script is designed to work with a structured Obsidian vault. It expects a hierarchy similar to this:

```text
Vault Root
+---Academics
|   +---BCom
|   |   +---Flashcards (Output Directory)
|   |   \---Semester One
|   |       +---ACCT1001
|   |       |   +---Live Lectures
|   |       |   \---Recorded Lectures
|   \---Concepts (Source for linked concepts)
```

> **Note:** The script uses relative paths, so it should be placed in a `_scripts` folder (or similar) at the root of your vault, or configured accordingly.

## ⚙️ Configuration

Configuration is centralized in `mcq_flashcards/core/config.py`. The script automatically detects the vault root relative to its own location:

```python
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent
VAULT_ROOT = Path(os.getenv("VAULT_ROOT", str(SCRIPT_DIR.parent)))  # v3.17.0: Environment variable support
```

You can also configure:
*   `DEFAULT_MODEL`: The Ollama model to use (default: `llama3:8b`).
*   `DEFAULT_WORKERS`: Number of threads for parallel processing.
*   `CACHE_DIR`: Location for caching LLM responses (JSON format for security - v3.15.0).
*   `VAULT_ROOT`: Override via environment variable for flexible deployment.

## 🏃 Usage

1.  **Start Ollama**: `ollama serve`
2.  **Run the Script**: `python mcq_flashcards.py`
3.  **Select Semester**: Choose your semester (or press Enter for default).
4.  **Select Subject**: Enter the subject code (e.g., `ACCT1001`) or press Enter for ALL subjects.
5.  **Select Week**: Enter a week number or press Enter for all weeks.
6.  **Select Study Mode**: Choose from Exam Prep, Quick Review, Deep Study, Mixed, or Custom (Bloom's + Difficulty).

The script will:
- Generate flashcards for selected subjects/weeks
- Apply Bloom's taxonomy and difficulty targeting
- Automatically post-process output to fix formatting issues
- Verify output quality with strict validation
- Display performance metrics (duration, questions/minute)
- Report statistics and any issues found

## 📄 Output Format

The script generates Markdown files (`{Subject}_W{Week}_MCQ.md`) with the following plugin-compliant structure:

```markdown
---
tags:
- flashcard/SUBJECT/Wxx
---
## MCQs: SUBJECT - Week X

### Note Title

Question text?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
?
**Answer:** 2) Option 2 Text
> **Explanation:** Short explanation of why this is the correct answer.
```

## 🧪 Testing

The project includes comprehensive automated tests to ensure code quality and reliability.

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_mcq_validator.py

# Run with coverage (requires pytest-cov)
pip install pytest-cov
pytest --cov=mcq_flashcards --cov-report=html
```

### Test Coverage

The test suite includes **101 comprehensive tests** covering:

- **Unit Tests (47 tests)**
  - MCQCleaner (15 tests) - Text cleaning and formatting
  - MCQValidator (14 tests) - Format validation with strict checks
  - AutoTuner (13 tests) - Performance optimization
  - Cache Management (4 tests) - JSON cache operations
  - Configuration (3 tests) - Input validation
  - Logging (3 tests) - Log rotation and setup
  - Metrics (3 tests) - Performance tracking

- **Integration Tests (54 tests)**
  - OllamaClient (9 tests) - API interaction and retries
  - FlashcardGenerator (10 tests) - End-to-end generation
  - PostProcessor (9 tests) - Output cleanup
  - CLI (14 tests) - User interface and argument parsing
  - Prompts (12 tests) - Template validation

All tests run in < 2 seconds with no external dependencies required.

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

**Latest:** v3.20.0 (2025-12-05) - Code Review Improvements
- Enhanced reliability, performance, and maintainability
- 101 tests passing
- Improved security (JSON cache), logging, validation, and performance metrics

## Credits

This project was vibecoded on Google Antigravity, with help from ChatGPT, Claude Sonnet, Mistral, and Qwen.