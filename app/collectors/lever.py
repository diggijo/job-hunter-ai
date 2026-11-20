import time
import httpx

from app.models import Job
from app.utils import html_to_text



def build_lever_description(posting):
    sections = []

    main_description = posting.get("descriptionPlain") or ""

    if not main_description.strip():
        main_description = html_to_text(
            posting.get("descriptionBody")
            or posting.get("description")
            or ""
        )

    if main_description.strip():
        sections.append(main_description.strip())

    for section in posting.get("lists") or []:
        heading = section.get("text") or ""
        content = html_to_text(section.get("content") or "")

        if heading.strip():
            sections.append(heading.strip())

        if content.strip():
            sections.append(content.strip())

    additional = posting.get("additionalPlain") or ""

    if not additional.strip():
        additional = html_to_text(
            posting.get("additional") or ""
        )

    if additional.strip():
        sections.append(additional.strip())

    return "\n\n".join(sections)


def get_lever_jobs(board_name, company_name=None, title_filter=None):
    url = f"https://api.lever.co/v0/postings/{board_name}"

    for attempt in range(3):
        try:
            response = httpx.get(
                url,
                params={"mode": "json"},
                timeout=15.0,
            )
            response.raise_for_status()
            break

        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                print(f"Skipping unavailable Lever board: {board_name}")
                return None

            if error.response.status_code not in (429, 500, 502, 503, 504):
                raise

            if attempt == 2:
                raise

            wait_seconds = 5 * (attempt + 1)
            print(
                f"Lever error for {board_name}. "
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

    if not isinstance(data, list):
        raise ValueError(f"Invalid Lever response for {board_name}")

    jobs = []

    for posting in data:
        title = posting["text"]

        if title_filter is not None and not title_filter(title):
            continue

        categories = posting.get("categories") or {}

        location = categories.get("location") or "Unknown"

        job = Job(
            title=title,
            company=company_name or board_name,
            location=location,
            description=build_lever_description(posting),
            url=posting["hostedUrl"],
            source="Lever",
            source_board_id=board_name,
            external_job_id=str(posting["id"]),
        )

        jobs.append(job)

    return jobs