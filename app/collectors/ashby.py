import time
import httpx
from app.models import Job


def get_ashby_jobs(board_name, company_name=None, title_filter=None):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board_name}"

    for attempt in range(3):
        try:
            response = httpx.get(url, timeout=15.0)
            response.raise_for_status()
            break

        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                print(f"Skipping unavailable Ashby board: {board_name}")
                return None

            if error.response.status_code not in (429, 500, 502, 503, 504):
                raise

            if attempt == 2:
                raise

            wait_seconds = 5 * (attempt + 1)
            print(
                f"Ashby error for {board_name}. "
                f"Retrying in {wait_seconds} seconds...",
                flush=True,
            )
            time.sleep(wait_seconds)

        except httpx.RequestError as error:
            if attempt == 2:
                raise

            wait_seconds = 5 * (attempt + 1)
            print(
                f"Connection error for {board_name}: {error}. "
                f"Retrying in {wait_seconds} seconds...",
                flush=True,
            )
            time.sleep(wait_seconds)

    data = response.json()

    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise ValueError(f"Invalid Ashby response for {board_name}")

    jobs = []

    for posting in data["jobs"]:
        if posting.get("isListed") is False:
            continue

        title = posting["title"]

        if title_filter is not None and not title_filter(title):
            continue

        job = Job(
            title=title,
            company=company_name or board_name,
            location=posting.get("location") or "Unknown",
            description=posting.get("descriptionPlain") or "",
            url=posting["jobUrl"],
            source="Ashby",
            source_board_id=board_name,
            external_job_id=str(posting["id"]),
        )

        jobs.append(job)

    return jobs
