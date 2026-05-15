import unittest
from types import SimpleNamespace
from unittest.mock import patch

import scraper


class TestScraper(unittest.TestCase):
    def test_clean_html_removes_tags(self) -> None:
        result = scraper.clean_html("<p>Hello <b>World</b></p>")
        self.assertEqual(result, "Hello World")

    @patch("scraper.feedparser.parse")
    def test_parse_feed_handles_request_exception(self, mock_parse) -> None:
        mock_parse.side_effect = RuntimeError("network down")

        result = scraper._parse_feed("https://example.com/feed.rss")

        self.assertIsNone(result)

    @patch("scraper.feedparser.parse")
    def test_parse_feed_handles_http_error_status(self, mock_parse) -> None:
        mock_parse.return_value = SimpleNamespace(status=503, bozo=False, entries=[])

        result = scraper._parse_feed("https://example.com/feed.rss")

        self.assertIsNone(result)

    @patch("scraper.feedparser.parse")
    def test_parse_feed_handles_bozo_feed(self, mock_parse) -> None:
        mock_parse.return_value = SimpleNamespace(
            status=200,
            bozo=True,
            bozo_exception=ValueError("invalid xml"),
            entries=[],
        )

        result = scraper._parse_feed("https://example.com/feed.rss")

        self.assertIsNone(result)

    @patch("scraper.FEEDS", ["https://feed-1", "https://feed-2"])
    @patch("scraper.feedparser.parse")
    def test_fetch_jobs_filters_and_truncates_results(self, mock_parse) -> None:
        long_description = "a" * 220 + " script"

        feed_one = SimpleNamespace(
            status=200,
            bozo=False,
            entries=[
                {
                    "title": "Simple API script",
                    "link": "https://job-1",
                    "description": "<p>Build a simple bot</p>",
                },
                {
                    "title": "Senior platform architect",
                    "link": "https://job-2",
                    "description": "<p>enterprise systems</p>",
                },
            ],
        )
        feed_two = SimpleNamespace(
            status=200,
            bozo=False,
            entries=[
                {
                    "title": "No keyword here",
                    "link": "https://job-3",
                    "description": f"<p>{long_description}</p>",
                }
            ],
        )

        mock_parse.side_effect = [feed_one, feed_two]

        jobs = scraper.fetch_jobs()

        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0]["title"], "Simple API script")
        self.assertEqual(jobs[0]["description_snippet"], "Build a simple bot")
        self.assertEqual(len(jobs[1]["description_snippet"]), 203)
        self.assertTrue(jobs[1]["description_snippet"].endswith("..."))


if __name__ == "__main__":
    unittest.main()
