import subprocess
import sys
import time
from pathlib import Path

from app.database import get_greenhouse_boards


PROGRESS_FILE = Path("data/collection_progress.txt")

BATCH_SIZE = 25
DELAY_SECONDS = 5


def get_next_batch():
    if PROGRESS_FILE.exists():
        return int(PROGRESS_FILE.read_text().strip())

    return 0


def save_next_batch(batch_number):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(str(batch_number))


total_boards = len(get_greenhouse_boards())
total_batches = (total_boards + BATCH_SIZE - 1) // BATCH_SIZE

start_batch = get_next_batch()

print(f"Total Greenhouse boards: {total_boards}", flush=True)
print(f"Total batches: {total_batches}", flush=True)
print(f"Resuming from batch {start_batch}", flush=True)

for batch_number in range(start_batch, total_batches):
    print(
        f"\nStarting batch {batch_number} of {total_batches - 1}...",
        flush=True
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.collect_jobs",
            str(batch_number)
        ],
        check=False
    )

    if result.returncode != 0:
        print(
            f"Batch {batch_number} failed. Progress not advanced.",
            flush=True
        )
        break

    save_next_batch(batch_number + 1)

    print(f"Batch {batch_number} completed.", flush=True)

    if batch_number < total_batches - 1:
        time.sleep(DELAY_SECONDS)

else:
    print("\nAll Greenhouse batches completed!", flush=True)