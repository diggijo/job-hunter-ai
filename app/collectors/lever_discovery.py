import time
import random
import httpx
from urllib.parse import urlparse, unquote

from app.database import add_lever_board


LEVER_DOMAINS = {"jobs.lever.co", "jobs.eu.lever.co"}


def extract_lever_token(url: str) -> str | None:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return None

    if parsed.hostname not in LEVER_DOMAINS:
        return None

    parts = parsed.path.strip("/").split("/")

    if not parts or not parts[0]:
        return None

    return unquote(parts[0])



def validate_lever_token(board_token: str) -> bool:
    url = f"https://api.lever.co/v0/postings/{board_token}"

    for attempt in range(3):
        try:
            response = httpx.get(
                url,
                params={"mode": "json", "limit": 1},
                timeout=10.0,
            )

            if response.status_code == 404:
                return False

            if response.status_code == 429 or response.status_code >= 500:
                if attempt == 2:
                    raise RuntimeError(
                        f"Lever API unavailable for {board_token}: "
                        f"HTTP {response.status_code}"
                    )

                retry_after = response.headers.get("Retry-After")

                try:
                    delay = float(retry_after) if retry_after else 2 ** attempt
                except ValueError:
                    delay = 2 ** attempt

                time.sleep(min(max(delay, 1), 60) + random.uniform(0, 0.5))
                continue

            response.raise_for_status()
            return isinstance(response.json(), list)

        except (httpx.TimeoutException, httpx.NetworkError) as error:
            if attempt == 2:
                raise RuntimeError(
                    f"Lever API request failed for {board_token}"
                ) from error

            time.sleep(2 ** attempt)

        except (httpx.HTTPStatusError, ValueError):
            return False

    return False



def save_discovered_lever_board(
    url: str,
    company_name: str,
) -> bool:
    board_token = extract_lever_token(url)

    if board_token is None:
        print(f"Not a Lever URL: {url}")
        return False

    if not validate_lever_token(board_token):
        print(f"Invalid Lever board: {board_token}")
        return False

    added = add_lever_board(board_token, company_name)

    if added:
        print(f"New Lever board saved: {board_token}")
    else:
        print(f"Lever board already exists: {board_token}")

    return added
