from collections import Counter
from app.database import get_jobs, get_candidate_profile
from app.matching import get_matching_jobs
from app.ai_matching import meets_experience_requirement
from app.config import EXCLUDED_JOB_KEYWORDS
from app.job_filters import get_job_priority

import re


candidate = get_candidate_profile()
jobs = get_jobs()

matches = get_matching_jobs(jobs, candidate)

filtered = [
    match for match in matches
    if match["job"]["company"] != "Test Company"
    and meets_experience_requirement(match["job"]["description"])
    and not EXCLUDED_JOB_KEYWORDS.intersection(
        re.findall(r"[a-z]+", match["job"]["title"].lower())
    )
]

filtered.sort(
    key=lambda match: get_job_priority(match["job"]["title"])
)

priority_counts = Counter(
    get_job_priority(match["job"]["title"])
    for match in filtered
)

print("\nJobs by priority:")
print(f"High priority: {priority_counts[1]}")
print(f"Medium priority: {priority_counts[2]}")
print(f"Lower priority: {priority_counts[3]}")

company_counts = Counter(
    match["job"]["company"]
    for match in filtered
)

print(f"Total jobs in database: {len(jobs)}")
print(f"Jobs matching title and location: {len(matches)}")
print(f"Jobs remaining after exclusions: {len(filtered)}")

print("\nJobs by company:")

for company, count in company_counts.most_common():
    print(f"{company}: {count}")

print("\nAll shortlisted technical jobs:")

for match in filtered:
    job = match["job"]

    print(
        f"{job['company']} | "
        f"{job['title']} | "
        f"{job['location']}"
    )