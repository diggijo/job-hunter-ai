import html
import httpx
import time
from app.models import Job
from app.utils import html_to_text


def get_greenhouse_jobs(board_token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    for attempt in range(3):
        try:
            response = httpx.get(url, timeout=15.0)
            response.raise_for_status()
            break

        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                print(f"Skipping unavailable Greenhouse board: {board_token}")
                return []

            if error.response.status_code not in (429, 500, 502, 503, 504):
                raise

            if attempt == 2:
                raise

            wait_seconds = 5 * (attempt + 1)
            print(
                f"Greenhouse error for {board_token}. "
                f"Retrying in {wait_seconds} seconds...",
                flush=True
            )
            time.sleep(wait_seconds)

        except httpx.RequestError as error:
            if attempt == 2:
                raise

            wait_seconds = 5 * (attempt + 1)
            print(
                f"Connection error for {board_token}: {error}. "
                f"Retrying in {wait_seconds} seconds...",
                flush=True
            )
            time.sleep(wait_seconds)

    data = response.json()

    jobs = []

    for greenhouse_job in data["jobs"]:
        description_html = html.unescape(greenhouse_job["content"])
        description = html_to_text(description_html)

        job = Job(
            title = greenhouse_job["title"],
            company = greenhouse_job["company_name"],
            location=(greenhouse_job.get("location") or {}).get("name") or "Unknown",
            description = description,
            url = greenhouse_job["absolute_url"],
            source = "Greenhouse"
        )

        jobs.append(job)

    return jobs