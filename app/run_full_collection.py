import subprocess
import sys
import time
from pathlib import Path

from app.config import BATCH_DELAY_SECONDS, BATCH_SIZE
from app.database import get_greenhouse_boards, get_ashby_boards


PROGRESS_FILE = Path("data/collection_progress.txt")
ASHBY_PROGRESS_FILE = Path("data/ashby_collection_progress.txt")


def get_next_batch():
    if PROGRESS_FILE.exists():
        return int(PROGRESS_FILE.read_text().strip())

    return 0


def save_next_batch(batch_number):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(str(batch_number))


def get_next_ashby_batch():
    if ASHBY_PROGRESS_FILE.exists():
        return int(ASHBY_PROGRESS_FILE.read_text().strip())

    return 0


def save_next_ashby_batch(batch_number):
    ASHBY_PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ASHBY_PROGRESS_FILE.write_text(str(batch_number))

    
total_boards = len(get_greenhouse_boards())
total_batches = (total_boards + BATCH_SIZE - 1) // BATCH_SIZE

start_batch = get_next_batch()

if start_batch >= total_batches:
    print("Previous collection completed. Starting a new collection cycle.", flush=True)
    start_batch = 0
    save_next_batch(0)

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
            "app.collect_greenhouse_batch",
            str(batch_number)
        ],
        check=False
    )

    if result.returncode != 0:
        print(
            f"Batch {batch_number} failed. Progress not advanced.",
            flush=True
        )
        sys.exit(result.returncode)

    save_next_batch(batch_number + 1)

    print(f"Batch {batch_number} completed.", flush=True)

    if batch_number < total_batches - 1:
        time.sleep(BATCH_DELAY_SECONDS)

else:
    print("\nAll Greenhouse batches completed!", flush=True)

total_ashby_boards = len(get_ashby_boards())
total_ashby_batches = (
    total_ashby_boards + BATCH_SIZE - 1
) // BATCH_SIZE

print(
    f"\nTotal Ashby boards: {total_ashby_boards}",
    flush=True,
)

start_ashby_batch = get_next_ashby_batch()

if start_ashby_batch >= total_ashby_batches:
    print("Previous Ashby collection completed. Starting a new cycle.", flush=True)
    start_ashby_batch = 0
    save_next_ashby_batch(0)

print(f"Resuming Ashby from batch {start_ashby_batch}", flush=True)

for batch_number in range(start_ashby_batch, total_ashby_batches):
    print(
        f"\nStarting Ashby batch {batch_number + 1} "
        f"of {total_ashby_batches}...",
        flush=True,
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.collect_ashby_batch",
            str(batch_number),
        ],
        check=False,
    )

    if result.returncode != 0:
        print(
            f"Ashby batch {batch_number} failed.",
            flush=True,
        )
        sys.exit(result.returncode)
    save_next_ashby_batch(batch_number + 1)

    print(
        f"Ashby batch {batch_number + 1} completed.",
        flush=True,
    )

    if batch_number < total_ashby_batches - 1:
        time.sleep(BATCH_DELAY_SECONDS)

print("\nAll Ashby batches completed!", flush=True)

