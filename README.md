# Quick Job Scraper

This is a simple Python script designed to help you find quick freelance programming and data tasks (like writing scripts, scraping, data entry, etc.) by parsing RSS feeds from job boards like We Work Remotely.

## Setup

1. **Install Python**: Make sure you have Python 3 installed.
2. **Install dependencies**: Use `pip` to install the required libraries.
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the scraper script:

```bash
python scraper.py
```

The script will fetch the latest jobs from several RSS feeds, filter them based on keywords (like "script", "bot", "data", "simple", "scrape", "api"), and print the matches to the console.

It will also save the found jobs to a `jobs.json` file in the same directory.
