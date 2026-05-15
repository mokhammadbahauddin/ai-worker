import unittest
import urllib.error
from io import BytesIO
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
        with patch("rtc_award_action.main.Path") as mock_path:
            wallet_file = mock_path.return_value.__truediv__.return_value
            wallet_file.exists.return_value = True
            wallet_file.is_file.return_value = True
            wallet_file.read_text.return_value = "# ignored\n\nfile_wallet\n"

            result = read_wallet_file("/workspace")
            self.assertEqual(result, "file_wallet")

    def test_read_wallet_file_missing(self):
        with patch("rtc_award_action.main.Path") as mock_path:
            wallet_file = mock_path.return_value.__truediv__.return_value
            wallet_file.exists.return_value = False
            wallet_file.is_file.return_value = False

            result = read_wallet_file("/workspace")
            self.assertIsNone(result)

    def test_read_wallet_file_only_comments(self):
        with patch("rtc_award_action.main.Path") as mock_path:
            wallet_file = mock_path.return_value.__truediv__.return_value
            wallet_file.exists.return_value = True
            wallet_file.is_file.return_value = True
            wallet_file.read_text.return_value = "# ignored\n\n# also ignored\n"

            result = read_wallet_file("/workspace")
            self.assertIsNone(result)

    def test_github_api_request_wraps_network_errors(self):
        with patch("rtc_award_action.main.urllib.request.urlopen", side_effect=urllib.error.URLError("dns error")):
            with self.assertRaises(RuntimeError):
                github_api_request("https://api.github.test", "token", {"body": "message"})

    def test_transfer_rtc_wraps_http_errors(self):
        err = urllib.error.HTTPError(
            url="https://node.example/api/transfer",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=BytesIO(b"boom"),
        )
        with patch("rtc_award_action.main.urllib.request.urlopen", side_effect=err):
            with self.assertRaises(RuntimeError):
                transfer_rtc("https://node.example", "from_wallet", "to_wallet", "20", "key")

    def test_transfer_rtc_wraps_network_errors(self):
        with patch("rtc_award_action.main.urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            with self.assertRaises(RuntimeError):
                transfer_rtc("https://node.example", "from_wallet", "to_wallet", "20", "key")


if __name__ == "__main__":
    unittest.main()
