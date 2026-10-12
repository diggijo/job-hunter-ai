import html
import httpx
from app.models import Job
from app.utils import html_to_text


def get_greenhouse_jobs(board_token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    response = httpx.get(url, timeout=15.0)
    response.raise_for_status()

    data = response.json()

    jobs = []

    for greenhouse_job in data["jobs"]:
        description_html = html.unescape(greenhouse_job["content"])
        description = html_to_text(description_html)

        job = Job(
            title = greenhouse_job["title"],
            company = greenhouse_job["company_name"],
            location = greenhouse_job["location"]["name"],
            description = description,
            url = greenhouse_job["absolute_url"],
            source = "Greenhouse"
        )

        jobs.append(job)

    return jobs