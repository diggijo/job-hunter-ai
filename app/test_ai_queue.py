from app.ai_matching import get_jobs_for_ai_analysis
from app.database import get_job_match_analysis


matches = get_jobs_for_ai_analysis(limit=30)

matches.sort(
    key=lambda match: (
        get_job_match_analysis(1, match["job"]["id"]) is not None
    )
)

print("\nFirst 15 jobs in evaluation queue:\n")

for match in matches[:15]:
    job = match["job"]
    analysis = get_job_match_analysis(1, job["id"])

    status = "NEW" if analysis is None else "CACHED"

    print(f"{status} | {job['company']} | {job['title']}")
