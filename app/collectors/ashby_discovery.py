import httpx
from urllib.parse import urlparse, unquote

from app.database import add_ashby_board


ASHBY_DOMAIN = "jobs.ashbyhq.com"


def extract_ashby_token(url: str) -> str | None:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return None

    if parsed.hostname != ASHBY_DOMAIN:
        return None

    parts = parsed.path.strip("/").split("/")

    if not parts or not parts[0]:
        return None

    return unquote(parts[0])


def validate_ashby_token(board_token: str) -> bool:
    url = (
        "https://api.ashbyhq.com/posting-api/"
        f"job-board/{board_token}"
    )

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()

        data = response.json()

        return (
            isinstance(data, dict)
            and isinstance(data.get("jobs"), list)
        )

    except (httpx.HTTPError, ValueError, AttributeError):
        return False


def save_discovered_ashby_board(
    url: str,
    company_name: str,
) -> bool:
    board_token = extract_ashby_token(url)

    if board_token is None:
        print(f"Not an Ashby URL: {url}")
        return False

    if not validate_ashby_token(board_token):
        print(f"Invalid Ashby board: {board_token}")
        return False

    added = add_ashby_board(board_token, company_name)

    if added:
        print(f"New Ashby board saved: {board_token}")
    else:
        print(f"Ashby board already exists: {board_token}")

    return added
