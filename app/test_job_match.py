from app.ai_service import analyse_job_match
from app.database import get_candidate_analysis, get_jobs, initialize_database, get_job_match_analysis, save_job_match_analysis
from app.models import Job


candidate_id = 1

candidate = get_candidate_analysis(candidate_id)

if candidate is None:
    raise ValueError("No saved candidate analysis found.")

jobs = get_jobs()

if not jobs:
    raise ValueError("No jobs found in the database.")

matching_jobs = [
    job for job in jobs
    if "software engineer" in job["title"].lower()
]

if not matching_jobs:
    raise ValueError("No software engineering jobs found.")

selected_job = matching_jobs[1]
job_id = selected_job["id"]

job = Job(
    title=selected_job["title"],
    company=selected_job["company"],
    location=selected_job["location"],
    description=selected_job["description"],
    url=selected_job["url"],
    source=selected_job["source"]
)

print(f"Evaluating: {job.title} at {job.company}")

initialize_database()

result = get_job_match_analysis(candidate_id, job_id)

if result is None:
    print("No saved match found. Calling Gemini...")

    result = analyse_job_match(candidate, job)

    save_job_match_analysis(candidate_id, job_id, result)

else:
    print("Using saved job match analysis.")

print(result.model_dump_json(indent=2))