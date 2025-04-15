# Wikidich Novel Scraper

A Python web scraper for extracting novel information and chapter content from [Wikidich.vn](https://wikidich.vn/).

## Features

- Scrape novel metadata (title, author, genre, chapter count, etc.)
- Extract chapter list with titles and URLs
- Download chapter content with proper formatting
- Save data in JSON and CSV formats
- Command-line interface with various options

## Requirements

- Python 3.6+
- Required packages:
  - requests
  - beautifulsoup4
  - pandas

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd wikidich-scraper
```

2. Install the required packages:
```
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python main.py
```

This will scrape the default novel URL (https://wikidich.vn/muc-than-ky-convert) and download the first 5 chapters.

### Advanced Options

```bash
python main.py --url <novel-url> --output <output-directory> --chapters <max-chapters> [--info-only]
```

- `--url`: URL of the novel page to scrape (default: https://wikidich.vn/muc-than-ky-convert)
- `--output`: Directory to save output files (default: output)
- `--chapters`: Maximum number of chapters to download (default: 5, use -1 for all)
- `--info-only`: Only scrape novel information, not chapter content

### Examples

Scrape a different novel:
```bash
python main.py --url https://wikidich.vn/some-other-novel
```

Download all chapters:
```bash
python main.py --chapters -1
```

Only get novel information (no chapter content):
```bash
python main.py --info-only
```

## Output Files

The scraper generates the following files in the output directory:

- `<novel_title>_info.json`: Basic novel information
- `<novel_title>_chapters.csv`: List of chapters with titles and URLs
- `<novel_title>_complete.json`: Complete novel data including chapter content
- `<novel_title>_chapters/`: Directory containing individual chapter JSON files

## Notes

- The scraper includes a delay between requests to avoid overwhelming the server.
- Make sure to respect the website's terms of service and robots.txt rules.
- This tool is for educational purposes only.

## License

MIT

---

## Chapter Enhancement (`enhance_chapters.py`)

This script enhances the downloaded chapter text using AI models (DeepSeek or Gemini).

### Setup

1.  **API Keys:** You need API keys for the service(s) you want to use.
    *   **DeepSeek:** Get a key from [https://platform.deepseek.com/](https://platform.deepseek.com/)
    *   **Gemini:** Get a key from [Google AI Studio](https://aistudio.google.com/)
2.  **Environment File:** Create a `.env` file in the project root:
    ```dotenv
    # .env file contents
    DEEPSEEK_API_KEY=YOUR_DEEPSEEK_KEY_HERE
    GOOGLE_API_KEY=YOUR_GEMINI_KEY_HERE
    ```
    *Make sure to add `.env` to your `.gitignore` file.* 
3.  **Install Dependencies:** Ensure all requirements, including `openai` and `google-generativeai`, are installed:
    ```bash
    pip3 install -r requirements.txt
    ```
4.  **Base Prompt:** Review and modify the enhancement instructions in `prompt/translate.prompt.txt` if needed.
5.  **Configuration:** Edit the `enhance_chapters.py` script to:
    *   Verify/update the `INPUT_DIR` (where raw chapters are) and `OUTPUT_DIR` (where enhanced chapters will be saved).
    *   Verify/update the `DEEPSEEK_MODEL_NAME` and `GEMINI_MODEL_NAME` constants.
    *   **Verify/update the pricing constants** (`DEEPSEEK_INPUT_PRICE`, `DEEPSEEK_OUTPUT_PRICE`, `GEMINI_INPUT_PRICE`, `GEMINI_OUTPUT_PRICE`) based on current official pricing for accurate cost estimation.

### Usage

```bash
python3 enhance_chapters.py [options]
```

**Options:**

*   `--provider {deepseek,gemini}`: Select the API provider (default: `deepseek`).
*   `-c CHAPTER, --chapter CHAPTER`: Process only a single specified chapter filename (e.g., `chapter_1478.txt`). Cannot be used with `-s` or `-o`.
*   `-s START_CHAPTER, --start-chapter START_CHAPTER`: Specify the filename of the chapter to start processing from (e.g., `chapter_1000.txt`).
*   `-o OFFSET, --offset OFFSET`: Process a specific number of chapters, starting from `--start-chapter`. Requires `--start-chapter`.
*   `--limit LIMIT`: Maximum number of concurrent API calls (default: 10).

**Examples:**

*   Enhance all chapters using DeepSeek (default):
    ```bash
    python3 enhance_chapters.py
    ```
*   Enhance a single chapter using DeepSeek:
    ```bash
    python3 enhance_chapters.py -c chapter_1478.txt
    ```
*   Enhance chapters 1500 to the end using Gemini:
    ```bash
    python3 enhance_chapters.py --provider gemini -s chapter_1500.txt
    ```
*   Enhance 20 chapters starting from 1600 using DeepSeek with 5 concurrent calls:
    ```bash
    python3 enhance_chapters.py -s chapter_1600.txt -o 20 --limit 5
    ```

### Output

Enhanced chapters are saved in the directory specified by `OUTPUT_DIR` in the script (default: `enhance_output`). The script logs token usage and estimated costs for each call and provides a final summary. 