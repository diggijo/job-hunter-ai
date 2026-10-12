from app.collectors.greenhouse import get_greenhouse_jobs
from app.database import add_job


greenhouse_boards = [
    "boxinc",
    "anthropic",
    "vercel",
    "neo4j",
    "drweng",
    "virtu"
    ]

added_count = 0
updated_count = 0
unchanged_count = 0
found_count = 0

for board_token in greenhouse_boards:
    jobs = get_greenhouse_jobs(board_token)

    found_count += len(jobs)

    for job in jobs:
        status = add_job(job)

        if status == "Added":
            added_count += 1
        elif status == "Updated":
            updated_count += 1
        elif status == "Unchanged":
            unchanged_count += 1

print(f"Jobs found: {found_count}")
print(f"Jobs added: {added_count}")
print(f"Jobs updated: {updated_count}")
print(f"Jobs unchanged: {unchanged_count}")