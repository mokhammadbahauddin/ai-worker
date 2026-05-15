import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from rtc_award_action.main import find_wallet_in_pr_body, github_api_request, parse_bool, read_wallet_file, transfer_rtc


class TestRtcAwardAction(unittest.TestCase):
    def test_parse_bool(self):
        self.assertTrue(parse_bool("true"))
        self.assertTrue(parse_bool("1"))
        self.assertFalse(parse_bool("false"))
        self.assertFalse(parse_bool(""))

    def test_find_wallet_in_pr_body_with_standard_format(self):
        body = """
        ## Submission
        RTC Wallet: contributor_wallet-01
        """
        self.assertEqual(find_wallet_in_pr_body(body), "contributor_wallet-01")

    def test_find_wallet_in_pr_body_from_backticks(self):
        body = "Recipient Wallet: `wallet_name`"
        self.assertEqual(find_wallet_in_pr_body(body), "wallet_name")

    def test_read_wallet_file(self):
        with TemporaryDirectory() as tmp:
            wallet_file = Path(tmp) / ".rtc-wallet"
            wallet_file.write_text("# ignored\n\nfile_wallet\n", encoding="utf-8")
            result = read_wallet_file(tmp)
            self.assertEqual(result, "file_wallet")

    def test_read_wallet_file_missing(self):
        with TemporaryDirectory() as tmp:
            result = read_wallet_file(tmp)
            self.assertIsNone(result)

    def test_read_wallet_file_only_comments(self):
        with TemporaryDirectory() as tmp:
            wallet_file = Path(tmp) / ".rtc-wallet"
            wallet_file.write_text("# ignored\n\n# also ignored\n", encoding="utf-8")
            result = read_wallet_file(tmp)
            self.assertIsNone(result)

    def test_github_api_request_wraps_network_errors(self):
        with patch("rtc_award_action.main.urllib.request.urlopen", side_effect=urllib.error.URLError("dns error")):
            with self.assertRaises(RuntimeError) as err:
                github_api_request("https://api.github.test", "token", {"body": "message"})
            self.assertIn("network error", str(err.exception))
            self.assertIsInstance(err.exception.__cause__, urllib.error.URLError)

    def test_transfer_rtc_wraps_http_errors(self):
        err = urllib.error.HTTPError(
            url="https://node.example/api/transfer",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=BytesIO(b"boom"),
        )
        with patch("rtc_award_action.main.urllib.request.urlopen", side_effect=err):
            with self.assertRaises(RuntimeError) as wrapped:
                transfer_rtc("https://node.example", "from_wallet", "to_wallet", "20", "key")
            self.assertIn("HTTP 500", str(wrapped.exception))
            self.assertIn("boom", str(wrapped.exception))

    def test_transfer_rtc_wraps_network_errors(self):
        with patch("rtc_award_action.main.urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            with self.assertRaises(RuntimeError):
                transfer_rtc("https://node.example", "from_wallet", "to_wallet", "20", "key")


if __name__ == "__main__":
    unittest.main()
