
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from app.collectors.greenhouse import get_greenhouse_jobs
from app.config import MAX_WORKERS, BATCH_SIZE
from app.database import add_job, get_greenhouse_boards
from app.job_filters import is_technical_role


MAX_WORKERS = 4

added_count = 0
updated_count = 0
unchanged_count = 0
found_count = 0

boards = get_greenhouse_boards()

batch_number = int(sys.argv[1]) if len(sys.argv) > 1 else 0

start = batch_number * BATCH_SIZE
end = start + BATCH_SIZE

boards_to_collect = boards[start:end]

print(f"Batch number: {batch_number}")
print(f"Collecting boards {start + 1} to {min(end, len(boards))} of {len(boards)}")


def fetch_board(board_token):
    return get_greenhouse_jobs(
        board_token,
        title_filter=is_technical_role
    )


# Fetch Greenhouse boards concurrently.
# executor.map preserves input order and propagates errors.
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    results = executor.map(fetch_board, boards_to_collect)

    for board_token, jobs in zip(boards_to_collect, results):
        if jobs is None:
            continue

        found_count += len(jobs)

        # Database writes stay on the main thread.
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
