from app.collectors.greenhouse import get_greenhouse_jobs
from app.database import add_job


jobs = get_greenhouse_jobs("boxinc")

added_count = 0
duplicate_count = 0

for job in jobs:
    if add_job(job):
        added_count += 1
    else:
        duplicate_count += 1

print(f"Jobs Found: {len(jobs)}")
print(f"Jobs Added: {added_count}")
print(f"Duplicate Skipped: {duplicate_count}")