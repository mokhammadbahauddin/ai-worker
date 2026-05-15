import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


WALLET_BODY_PATTERNS = [
    re.compile(r"^\s*(?:rtc[-_ ]wallet|wallet)\s*[:=]\s*`?([A-Za-z0-9_.-]+)`?\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*(?:wallet[-_ ]name|recipient[-_ ]wallet)\s*[:=]\s*`?([A-Za-z0-9_.-]+)`?\s*$", re.IGNORECASE | re.MULTILINE),
]


def parse_bool(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def find_wallet_in_pr_body(pr_body: str) -> str | None:
    body = pr_body or ""
    for pattern in WALLET_BODY_PATTERNS:
        match = pattern.search(body)
        if match:
            return match.group(1).strip()
    return None


def read_wallet_file(workspace: str) -> str | None:
    wallet_file = Path(workspace) / ".rtc-wallet"
    if not wallet_file.exists() or not wallet_file.is_file():
        return None

    for line in wallet_file.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if candidate and not candidate.startswith("#"):
            return candidate
    return None


def github_api_request(url: str, token: str, payload: dict) -> tuple[int, str]:
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        error_text = err.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"GitHub API request failed with HTTP {err.code}: {error_text}") from err


def post_pr_comment(repo: str, issue_number: int, token: str, message: str) -> None:
    comments_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    github_api_request(comments_url, token, {"body": message})


def transfer_rtc(node_url: str, wallet_from: str, wallet_to: str, amount: str, admin_key: str) -> tuple[int, str]:
    url = f"{node_url.rstrip('/')}/api/transfer"
    payload = {
        "from": wallet_from,
        "to": wallet_to,
        "amount": amount,
        "admin_key": admin_key,
        "asset": "RTC",
    }
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        return response.status, response.read().decode("utf-8")


def main() -> int:
    event_path = os.getenv("GITHUB_EVENT_PATH")
    repository = os.getenv("GITHUB_REPOSITORY", "")
    github_token = os.getenv("GITHUB_TOKEN", "")
    workspace = os.getenv("GITHUB_WORKSPACE", os.getcwd())

    node_url = os.getenv("INPUT_NODE_URL", "")
    amount = os.getenv("INPUT_AMOUNT", "")
    wallet_from = os.getenv("INPUT_WALLET_FROM", "")
    admin_key = os.getenv("INPUT_ADMIN_KEY", "")
    dry_run = parse_bool(os.getenv("INPUT_DRY_RUN", "false"))

    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH is not set")
    if not node_url or not amount or not wallet_from or not admin_key:
        raise RuntimeError("Missing required inputs: node-url, amount, wallet-from, admin-key")

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    pr = event.get("pull_request") or {}
    if not pr.get("merged"):
        print("Pull request is not merged; skipping reward.")
        return 0

    pr_number = pr.get("number") or event.get("number")
    pr_body = pr.get("body") or ""
    wallet_to = find_wallet_in_pr_body(pr_body) or read_wallet_file(workspace)

    if not wallet_to:
        raise RuntimeError("Could not determine recipient wallet from PR body or .rtc-wallet file")

    if not repository or not pr_number:
        raise RuntimeError("Missing repository or pull request number in event payload")

    if not github_token:
        raise RuntimeError("GITHUB_TOKEN is required to post PR comments")

    if dry_run:
        message = (
            f"🧪 Dry run: would transfer {amount} RTC from `{wallet_from}` "
            f"to `{wallet_to}` via `{node_url}`."
        )
        post_pr_comment(repository, int(pr_number), github_token, message)
        print(message)
        return 0

    try:
        status, body = transfer_rtc(node_url, wallet_from, wallet_to, amount, admin_key)
        message = (
            f"✅ RTC reward sent: transferred {amount} RTC from `{wallet_from}` "
            f"to `{wallet_to}` (status: {status})."
        )
        post_pr_comment(repository, int(pr_number), github_token, message)
        print(f"Transfer response status={status}, body={body[:500]}")
        return 0
    except urllib.error.HTTPError as err:
        error_text = err.read().decode("utf-8", errors="replace")[:500]
        failure_message = (
            f"❌ RTC reward transfer failed for `{wallet_to}`: HTTP {err.code}. "
            f"Please check node availability and credentials."
        )
        post_pr_comment(repository, int(pr_number), github_token, failure_message)
        print(f"Transfer failed HTTP {err.code}: {error_text}")
        raise
    except urllib.error.URLError as err:
        failure_message = (
            f"❌ RTC reward transfer failed for `{wallet_to}` due to network error: {err.reason}."
        )
        post_pr_comment(repository, int(pr_number), github_token, failure_message)
        print(f"Transfer failed with network error: {err.reason}")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
