from app.ai_matching import get_jobs_for_ai_analysis
from app.database import get_job_match_analysis, get_jobs


jobs = get_jobs_for_ai_analysis(limit=25)

for match in jobs:
    job = match["job"]
    cached = get_job_match_analysis(1, job["id"])

    if cached is None:
        status = "NOT EVALUATED"
    else:
        status = f"CACHED | {cached.eligibility} | Score: {cached.score}"

    print(f"{job['company']} | {job['title']} | {status}")

print("\nBlenheim Chalcot Graduate Data Engineer check:")

for job in get_jobs():
    if (
        job["company"] == "Blenheim Chalcot"
        and job["title"] == "Graduate Data Engineer"
    ):
        analysis = get_job_match_analysis(1, job["id"])
        print(f"Job ID: {job['id']}")
        print(f"Location: {job['location']}")
        print(f"Cached: {analysis is not None}")
        if analysis:
            print(f"Eligibility: {analysis.eligibility}")
            print(f"Score: {analysis.score}")