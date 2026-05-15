import feedparser
import json
import re

# Keywords indicating potentially quick / small tasks
KEYWORDS = ["script", "data", "bot", "simple", "scrape", "scraping", "entry", "easy", "api"]

# We Work Remotely RSS feed for programming jobs
FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-data-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-finance-and-legal-jobs.rss"
]

def clean_html(raw_html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=' ', strip=True)

def fetch_jobs():
    found_jobs = []

    for feed_url in FEEDS:
        print(f"Fetching {feed_url}...")
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            description_html = entry.get("description", "")

            description = clean_html(description_html)

            # Combine title and description to check for keywords
            text_to_search = (title + " " + description).lower()

            if any(keyword in text_to_search for keyword in KEYWORDS):
                job_data = {
                    "title": title,
                    "link": link,
                    "description_snippet": description[:200] + "..." if len(description) > 200 else description
                }
                found_jobs.append(job_data)

    return found_jobs

if __name__ == "__main__":
    jobs = fetch_jobs()

    if jobs:
        print(f"\nFound {len(jobs)} jobs that match your keywords!\n")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['title']}")
            print(f"   Link: {job['link']}")
            print(f"   Snippet: {job['description_snippet']}\n")

        with open("jobs.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=4, ensure_ascii=False)
        print("Results saved to jobs.json")
    else:
        print("No quick jobs found at this time.")
