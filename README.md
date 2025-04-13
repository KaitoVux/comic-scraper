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