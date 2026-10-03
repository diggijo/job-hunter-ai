from app.database import get_candidate_profile, get_jobs
from app.matching import get_matching_jobs


profile = get_candidate_profile()
jobs = get_jobs()

matching_jobs = get_matching_jobs(jobs, profile)

for job in matching_jobs:
    print(f"{job['title']} - {job['company']} - {job['location']}")

print(f"\nMatching jobs: {len(matching_jobs)}")