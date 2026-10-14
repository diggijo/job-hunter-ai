import httpx
from app.database import add_greenhouse_board
from urllib.parse import urlparse


GREENHOUSE_DOMAINS = {
    "boards.greenhouse.io",
    "job-boards.greenhouse.io"
}


def extract_greenhouse_token(url: str) -> str | None:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return None

    if parsed.hostname not in GREENHOUSE_DOMAINS:
        return None

    path_parts = parsed.path.strip("/").split("/")

    if not path_parts or not path_parts[0]:
        return None

    return path_parts[0].lower()


def validate_greenhouse_token(board_token: str) -> bool:
    url = (
        f"https://boards-api.greenhouse.io/v1/boards/"
        f"{board_token}/jobs"
    )

    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()

        data = response.json()

        return isinstance(data.get("jobs"), list)

    except (httpx.HTTPError, ValueError, AttributeError):
        return False


def save_discovered_greenhouse_board(url: str) -> bool:
    board_token = extract_greenhouse_token(url)

    if board_token is None:
        print(f"Not a Greenhouse URL: {url}")
        return False

    if not validate_greenhouse_token(board_token):
        print(f"Invalid Greenhouse board: {board_token}")
        return False

    added = add_greenhouse_board(board_token)

    if added:
        print(f"New Greenhouse board saved: {board_token}")
    else:
        print(f"Greenhouse board already exists: {board_token}")

    return added