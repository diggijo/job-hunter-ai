import argparse
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
        raise RuntimeError(
            f"{len(failed_boards)} {provider.title()} boards failed. "
            "Batch will be retried."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Collect jobs from a provider batch."
    )

    parser.add_argument(
        "provider",
        choices=PROVIDERS.keys(),
    )

    parser.add_argument(
        "batch_number",
        type=int,
    )

    args = parser.parse_args()

    if args.batch_number < 0:
        parser.error("batch_number must be zero or greater")

    collect_batch(args.provider, args.batch_number)


if __name__ == "__main__":
    main()
