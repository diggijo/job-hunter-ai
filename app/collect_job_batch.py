import sys
import time
from app.collectors.greenhouse import get_greenhouse_jobs
from app.database import add_job, get_greenhouse_boards
from app.job_filters import is_technical_role


added_count = 0
updated_count = 0
unchanged_count = 0
found_count = 0

boards = get_greenhouse_boards()

batch_size = 25
batch_number = int(sys.argv[1]) if len(sys.argv) > 1 else 0

start = batch_number * batch_size
end = start + batch_size

boards_to_collect = boards[start:end]

print(f"Batch number: {batch_number}")
print(f"Collecting boards {start + 1} to {min(end, len(boards))} of {len(boards)}")

for board_token in boards_to_collect:
    jobs = get_greenhouse_jobs(board_token)

    time.sleep(1)

    if jobs is None:
        continue

    found_count += len(jobs)

    for job in jobs:
        if not is_technical_role(job.title):
            continue

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