
import sys
from concurrent.futures import ThreadPoolExecutor

from app.collectors.ashby import get_ashby_jobs
from app.config import MAX_WORKERS, BATCH_SIZE
from app.database import add_job, get_ashby_boards
from app.job_filters import is_technical_role


def collect_batch(batch_number: int):
    boards = get_ashby_boards()

    start = batch_number * BATCH_SIZE
    end = start + BATCH_SIZE
    boards_to_collect = boards[start:end]

    print(f"Ashby batch number: {batch_number}")
    print(
        f"Collecting boards {start + 1} to "
        f"{min(end, len(boards))} of {len(boards)}"
    )

    added_count = 0
    updated_count = 0
    unchanged_count = 0
    found_count = 0

    def fetch_board(board):
        board_token, company_name = board

        try:
            jobs = get_ashby_jobs(
                board_token,
                company_name=company_name,
                title_filter=is_technical_role,
            )
            return jobs, None

        except Exception as error:
            return None, f"{board_token}: {error}"

    failed_boards = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(fetch_board, boards_to_collect)

        for board, (jobs, error) in zip(boards_to_collect, results):
            if error is not None:
                print(f"Failed Ashby board: {error}", flush=True)
                failed_boards.append(board[0])
                continue

            if jobs is None:
                continue

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

    if failed_boards:
        print(
            f"Failed boards: {', '.join(failed_boards)}",
            flush=True,
        )
        raise RuntimeError(
            f"{len(failed_boards)} Ashby boards failed. "
            "Batch will be retried."
        )


if __name__ == "__main__":
    batch_number = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    collect_batch(batch_number)