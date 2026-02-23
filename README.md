# 🧠 Obsidian Spaced Repetition Flashcard Generator

**Turn your lecture notes into active recall tools instantly.**

This Python tool leverages local LLMs (via Ollama) to analyze your Obsidian vault, understand your lecture notes and linked concepts, and generate high-quality Multiple Choice Questions (MCQs). The output is perfectly formatted for the **[Obsidian Spaced Repetition](https://github.com/st3v3nmw/obsidian-spaced-repetition/)** plugin, allowing you to seamlessly integrate them into your study workflow.

🔗 **Repository:** [https://github.com/dencelkbabu/obsidian-spaced-repetition-flashcard-generator](https://github.com/dencelkbabu/obsidian-spaced-repetition-flashcard-generator)

## ✨ Key Features

### Core Features
*   **🤖 AI-Powered:** Uses Llama 3 (or any Ollama model) to generate grounded, accurate questions.
*   **🔗 Context-Aware:** Intelligently scans your lecture notes and follows `[[wikilinks]]` to generate concept-specific cards.
*   **📝 Obsidian Ready:** Outputs clean Markdown formatted strictly for the Spaced Repetition plugin.
*   **🎯 Bloom's Taxonomy (v3.11.0):** Target specific cognitive levels (Remember, Understand, Apply, Analyze, Evaluate, Create).
*   **🎚️ Difficulty Levels:** Choose Easy, Medium, Hard, or Mixed difficulty for your questions.

### Performance & Reliability
*   **⚡ High Performance:** Multi-threaded processing and smart JSON caching ensure fast subsequent runs.
*   **🚀 AutoTuner (v2.0):** Dynamically monitors GPU (Nvidia) and error rates to optimize performance.
*   **📊 Performance Metrics (v3.14.0):** Track generation speed, throughput (questions/minute), and progress.
*   **🔒 Secure Caching (v3.15.0):** JSON-based cache eliminates security risks of pickle serialization.

### Quality Assurance
*   **✅ Strict Validation (v3.10.0):** Enhanced validator ensures exactly 4 options, valid answers, and explanations.
*   **🔄 Self-Correction (v2.0):** Automatically detects invalid outputs and prompts the AI to fix them.
*   **🧹 Auto-Cleanup (v2.7):** Post-processor fixes LLM output inconsistencies and verifies quality.
*   **📊 Budget System (v4.0.0):** Generates exactly ~300 cards per subject, distributed proportionally across W01-W14.
*   **🧪 Comprehensive Testing (v3.20.0):** 173 automated tests ensure code quality and reliability.

### Developer Experience
*   **📦 Modular Architecture (v2.7):** Clean package structure for better maintainability and extensibility.
*   **🛠️ Robust & Portable:** Automatic retries, error handling, works on any OS (Windows/Mac/Linux).
*   **⚙️ Configurable Paths (v3.17.0):** Environment variable support for flexible deployment.
*   **🔧 Dev Mode:** Advanced features for testing and development (see Usage section).

## 🚀 Prerequisites

1.  **[Obsidian Spaced Repetition Plugin](https://github.com/st3v3nmw/obsidian-spaced-repetition/)**: Required for reviewing the flashcards.
2.  **Ollama**: Installed and running locally.
    *   Default Model: `llama3.1:8b` (Configurable).
3.  **Python 3.8+**: With the following dependencies:
```bash
pip install requests tqdm pytest
# Optional (for benchmark memory tracking):
pip install psutil
```

## 📂 Project Structure

```text
_scripts/
├── mcq_flashcards.py          # Backwards-compatible entry point
├── cli.py                     # Main CLI interface
├── pytest.ini                 # Test configuration
├── tests/                     # Test suite (173 tests)
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
*   `DEFAULT_MODEL`: The Ollama model to use (default: `llama3.1:8b`).
*   `DEFAULT_WORKERS`: Number of threads for parallel processing.
*   `SUBJECT_BUDGET`: Total cards to generate per subject (default: `300`).
*   `MIN_PER_ITEM` / `MAX_PER_ITEM`: Min/max questions per lecture or concept (default: `1`/`5`).
*   `SEMESTER_WEEKS`: Number of weeks in a semester (default: `14`).
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

### Development Mode

For advanced users and testing:

```bash
# Basic dev mode
python mcq_flashcards.py -d ACCT1001

# Specific week
python mcq_flashcards.py -d ACCT1001 5

# Clear cache before processing
python mcq_flashcards.py -d ACCT1001 --clear-cache

# Deep clear (cache only, no processing)
python mcq_flashcards.py -d ALL --deep-clear

# Custom Bloom's level and difficulty
python mcq_flashcards.py -d ACCT1001 --bloom analyze --difficulty hard

# Override semester
python mcq_flashcards.py -d ACCT1001 -s "Semester Two"
```

**Dev Mode Features:**
- Skip interactive prompts
- Direct subject/week specification
- Cache management (`--clear-cache`, `--deep-clear`)
- Bloom's taxonomy targeting (`--bloom`)
- Difficulty selection (`--difficulty`)
- Semester override (`-s`, `--semester`)
- Output to `_dev` folder (auto-cleaned on next run)

Run `python mcq_flashcards.py --help` for all options.


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

The test suite includes **173 comprehensive tests** covering unit, integration, and robustness tests across all modules.

All tests run in < 2 seconds with no external dependencies required.

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

**Latest:** v4.0.0 (2026-02-23) - Budget-Based Generation
- Generates ~300 cards per subject (was ~1,500+), fitting a 1-week study schedule
- 173 tests passing
- See [CHANGELOG.md](CHANGELOG.md) for full version history

## Credits

This project was vibecoded on Google Antigravity, with help from ChatGPT, Claude Sonnet, Mistral, and Qwen.