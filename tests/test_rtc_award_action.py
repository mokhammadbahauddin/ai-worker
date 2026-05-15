import unittest
from unittest.mock import patch

from rtc_award_action.main import find_wallet_in_pr_body, parse_bool, read_wallet_file


class TestRtcAwardAction(unittest.TestCase):
    def test_parse_bool(self):
        self.assertTrue(parse_bool("true"))
        self.assertTrue(parse_bool("1"))
        self.assertFalse(parse_bool("false"))
        self.assertFalse(parse_bool(""))

    def test_find_wallet_in_pr_body_from_label(self):
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


if __name__ == "__main__":
    unittest.main()
