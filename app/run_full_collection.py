import subprocess
import sys
import time
from pathlib import Path

from app.config import BATCH_DELAY_SECONDS, BATCH_SIZE
from app.database import (
    get_greenhouse_boards,
    get_ashby_boards,
    get_lever_boards,
)


PROVIDERS = {
    "greenhouse": {
        "get_boards": get_greenhouse_boards,
        "progress_file": Path("data/collection_progress.txt"),
    },
    "ashby": {
        "get_boards": get_ashby_boards,
        "progress_file": Path("data/ashby_collection_progress.txt"),
    },
    "lever": {
        "get_boards": get_lever_boards,
        "progress_file": Path("data/lever_collection_progress.txt"),
    },
}


def get_next_batch(progress_file: Path) -> int:
    if progress_file.exists():
        return int(progress_file.read_text().strip())

    return 0


def save_next_batch(progress_file: Path, batch_number: int):
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    progress_file.write_text(str(batch_number))


def collect_provider(provider: str, config: dict):
    boards = config["get_boards"]()
    progress_file = config["progress_file"]

    total_boards = len(boards)
    total_batches = (total_boards + BATCH_SIZE - 1) // BATCH_SIZE

    start_batch = get_next_batch(progress_file)

    if start_batch >= total_batches:
        print(
            f"Previous {provider.title()} collection completed. "
            "Starting a new collection cycle.",
            flush=True,
        )
        start_batch = 0
        save_next_batch(progress_file, 0)

    print(f"\nProvider: {provider.title()}", flush=True)
    print(f"Total boards: {total_boards}", flush=True)
    print(f"Total batches: {total_batches}", flush=True)
    print(f"Resuming from batch {start_batch}", flush=True)

    for batch_number in range(start_batch, total_batches):
        print(
            f"\nStarting {provider.title()} batch "
            f"{batch_number + 1} of {total_batches}...",
            flush=True,
        )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "app.collect_batches",
                provider,
                str(batch_number),
            ],
            check=False,
        )

        if result.returncode != 0:
            print(
                f"{provider.title()} batch {batch_number + 1} failed. "
                "Progress not advanced.",
                flush=True,
            )
            sys.exit(result.returncode)

        save_next_batch(progress_file, batch_number + 1)

        print(
            f"{provider.title()} batch "
            f"{batch_number + 1} completed.",
            flush=True,
        )

        if batch_number < total_batches - 1:
            time.sleep(BATCH_DELAY_SECONDS)

    print(
        f"\nAll {provider.title()} batches completed!",
        flush=True,
    )


def main():
    for provider, config in PROVIDERS.items():
        collect_provider(provider, config)

    print("\nAll provider batches completed!", flush=True)

    print("\nStarting failed-board retries...", flush=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.collect_batches",
            "--retry-failed",
        ],
        check=False,
    )

    if result.returncode != 0:
        print(
            "Failed-board retry process encountered an error.",
            flush=True,
        )
        sys.exit(result.returncode)

    print("\nAll collection processing finished!", flush=True)


if __name__ == "__main__":
    main()