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

## 🚀 Prerequisites

1.  **[Obsidian Spaced Repetition Plugin](https://github.com/st3v3nmw/obsidian-spaced-repetition/)**: Required for reviewing the flashcards.
2.  **Ollama**: Installed and running locally.
    *   Default Model: `llama3:8b` (Configurable).
3.  **Python 3.8+**: With the following dependencies:
```bash
pip install requests pyyaml tqdm
```

## 📂 Folder Structure

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

Open `mcq_flashcards.py` to adjust settings. The script automatically detects the vault root relative to its own location:

```python
SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
```

You can also configure:
*   `MODEL`: The Ollama model to use (default: `llama3:8b`).
*   `MAX_WORKERS`: Number of threads for parallel processing.
*   `CACHE_DIR`: Location for caching LLM responses.

## 🏃 Usage

1.  **Start Ollama**: `ollama serve`
2.  **Run the Script**: `python mcq_flashcards.py`
3.  **Select Subject**: Enter the subject code (e.g., `ACCT1001`).
4.  **Select Week**: Enter a week number or press Enter for all.

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

## Credits

This project was vibecoded on Google Antigravity, with help from ChatGPT, Mistral, Qwen.