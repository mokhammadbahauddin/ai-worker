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

## Reusable GitHub Action: Award RTC on Merged PRs

This repository also provides a reusable GitHub Action at `action.yml` that awards RTC when a pull request is merged.

Required inputs:
- `node-url`
- `amount`
- `wallet-from`
- `admin-key`
- `dry-run` (optional, default `false`)

Wallet resolution order:
1. PR body line like `RTC Wallet: your_wallet_name`
2. `.rtc-wallet` file in the repository root (first non-empty, non-comment line)

Caller workflow should grant permission to create PR comments:

```yaml
permissions:
  pull-requests: write
```
