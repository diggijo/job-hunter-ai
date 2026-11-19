import argparse
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app.collectors.ashby import get_ashby_jobs
from app.collectors.greenhouse import get_greenhouse_jobs
from app.collectors.lever import get_lever_jobs

from app.config import BATCH_SIZE, MAX_WORKERS
from app.database import (
    add_job,
    get_ashby_boards,
    get_greenhouse_boards,
    get_lever_boards,
)
from app.job_filters import is_technical_role


PROVIDERS = {
    "greenhouse": {
        "get_boards": get_greenhouse_boards,
        "get_jobs": get_greenhouse_jobs,
    },
    "ashby": {
        "get_boards": get_ashby_boards,
        "get_jobs": get_ashby_jobs,
    },
    "lever": {
        "get_boards": get_lever_boards,
        "get_jobs": get_lever_jobs,
    },
}

FAILED_BOARDS_FILE = Path("data/failed_collection_boards.json")


def write_failed_boards(failures: dict):
    FAILED_BOARDS_FILE.parent.mkdir(parents=True, exist_ok=True)

    temp_file = FAILED_BOARDS_FILE.with_suffix(".tmp")

    temp_file.write_text(
        json.dumps(failures, indent=2),
        encoding="utf-8",
    )

    temp_file.replace(FAILED_BOARDS_FILE)


def save_failed_boards(provider: str, board_tokens: list[str]):
    if not board_tokens:
        return

    FAILED_BOARDS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if FAILED_BOARDS_FILE.exists():
        failures = json.loads(FAILED_BOARDS_FILE.read_text())
    else:
        failures = {}

    existing = failures.get(provider, [])
    failures[provider] = list(dict.fromkeys(existing + board_tokens))

    write_failed_boards(failures)


def retry_failed_boards():
    if not FAILED_BOARDS_FILE.exists():
        print("No failed boards to retry.", flush=True)
        return

    failures = json.loads(FAILED_BOARDS_FILE.read_text())

    for provider, board_tokens in failures.items():
        if not board_tokens:
            continue

        print(
            f"Retrying {len(board_tokens)} failed {provider.title()} boards...",
            flush=True,
        )

        config = PROVIDERS[provider]
        boards = config["get_boards"]()

        if provider == "greenhouse":
            board_lookup = {token: token for token in boards}
        else:
            board_lookup = {
                token: (token, company)
                for token, company in boards
            }

        for token in board_tokens:
            board = board_lookup.get(token)

            if board is None:
                print(
                    f"Board no longer registered: {token}",
                    flush=True,
                )
                continue

            try:
                if provider == "greenhouse":
                    jobs = config["get_jobs"](
                        token,
                        title_filter=is_technical_role,
                    )
                else:
                    jobs = config["get_jobs"](
                        token,
                        company_name=board[1],
                        title_filter=is_technical_role,
                    )

                if jobs is None:
                    raise RuntimeError("Collector returned no result")


            except Exception as error:
                print(
                    f"Retry failed: {provider}/{token}: {error}",
                    flush=True,
                )
                continue

            for job in jobs:
                add_job(job)

            print(f"Retry succeeded: {provider}/{token}", flush=True)

            failures[provider] = [
                failed_token
                for failed_token in failures[provider]
                if failed_token != token
            ]

            write_failed_boards(failures)

    total_remaining = sum(len(tokens) for tokens in failures.values())

    print(
        f"Failed-board retries finished. "
        f"{total_remaining} boards still unsuccessful.",
        flush=True,
    )


def collect_batch(provider: str, batch_number: int):
    config = PROVIDERS[provider]

    boards = config["get_boards"]()

    start = batch_number * BATCH_SIZE
    end = start + BATCH_SIZE

    boards_to_collect = boards[start:end]

    print(
        f"{provider.title()} batch number: {batch_number}",
        flush=True,
    )
    print(
        f"Collecting boards {start + 1} to "
        f"{min(end, len(boards))} of {len(boards)}",
        flush=True,
    )

    counts = {
        "Added": 0,
        "Updated": 0,
        "Unchanged": 0,
    }

    found_count = 0
    failed_boards = []

    def fetch_board(board):
        if provider == "greenhouse":
            board_token = board
            company_name = None
        else:
            board_token, company_name = board

        try:
            if provider == "greenhouse":
                jobs = config["get_jobs"](
                    board_token,
                    title_filter=is_technical_role,
                )
            else:
                jobs = config["get_jobs"](
                    board_token,
                    company_name=company_name,
                    title_filter=is_technical_role,
                )

            return jobs, None

        except Exception as error:
            return None, f"{board_token}: {error}"

    # Fetch boards concurrently.
    # Database writes remain on the main thread.
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(fetch_board, boards_to_collect)

        for board, (jobs, error) in zip(boards_to_collect, results):
            if error is not None:
                print(
                    f"Failed {provider.title()} board: {error}",
                    flush=True,
                )

                board_token = (
                    board if provider == "greenhouse" else board[0]
                )
                failed_boards.append(board_token)
                continue

            if jobs is None:
                continue

            found_count += len(jobs)

            for job in jobs:
                status = add_job(job)

                if status in counts:
                    counts[status] += 1

    print(f"Jobs found: {found_count}", flush=True)
    print(f"Jobs added: {counts['Added']}", flush=True)
    print(f"Jobs updated: {counts['Updated']}", flush=True)
    print(f"Jobs unchanged: {counts['Unchanged']}", flush=True)

    if failed_boards:
        print(
            f"Failed boards: {', '.join(failed_boards)}",
            flush=True,
        )

    save_failed_boards(provider, failed_boards)
    return failed_boards


def main():
    parser = argparse.ArgumentParser(
        description="Collect jobs from a provider batch."
    )

    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry previously failed boards.",
    )

    parser.add_argument(
        "provider",
        nargs="?",
        choices=PROVIDERS.keys(),
    )

    parser.add_argument(
        "batch_number",
        nargs="?",
        type=int,
    )

    args = parser.parse_args()

    if args.retry_failed:
        if args.provider is not None or args.batch_number is not None:
            parser.error("--retry-failed cannot be combined with a batch")
        retry_failed_boards()
        return

    if args.provider is None or args.batch_number is None:
        parser.error("provider and batch_number are required")

    if args.batch_number < 0:
        parser.error("batch_number must be zero or greater")

    collect_batch(args.provider, args.batch_number)


if __name__ == "__main__":
    main()
