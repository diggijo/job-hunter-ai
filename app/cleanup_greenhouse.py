
import argparse
import sqlite3

from app.check_closed_jobs import check_board, commit_closed_job_deletions


def get_eligible_boards(database_path, limit):
    connection = sqlite3.connect(
        f"file:{database_path}?mode=ro",
        uri=True,
    )

    try:
        rows = connection.execute(
            """
            SELECT source_board_id
            FROM jobs
            WHERE source = 'Greenhouse'
              AND source_board_id IS NOT NULL
              AND TRIM(source_board_id) != ''
              AND external_job_id IS NOT NULL
            GROUP BY source_board_id
            HAVING COUNT(*) >= 5
            ORDER BY source_board_id
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [row[0] for row in rows]

    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(
        description="Dry-run Greenhouse closed-job cleanup."
    )

    parser.add_argument("--limit", type=int, default=5)

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete confirmed closed jobs instead of running a dry-run.",
    )
    args = parser.parse_args()

    if args.delete:
        confirmation = input(
            "This will permanently delete eligible closed Greenhouse jobs. "
            "Type DELETE to continue: "
        )

        if confirmation != "DELETE":
            print("Deletion cancelled.")
            return

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    database_path = "data/jobhunter.db"
    boards = get_eligible_boards(database_path, args.limit)

    print(f"Checking {len(boards)} Greenhouse boards")
    if args.delete:
        print("LIVE CLEANUP - eligible closed jobs will be deleted")
    else:
        print("DRY RUN ONLY - no jobs will be deleted")

    counts = {
        "eligible": 0,
        "blocked": 0,
        "skipped": 0,
        "failed": 0,
    }
    total_candidates = 0
    total_deleted = 0

    for index, board_token in enumerate(boards, 1):
        print(f"\n[{index}/{len(boards)}] {board_token}")

        try:
            result = check_board(board_token)

            # Support the old string return format during migration.
            if isinstance(result, str):
                status = result
                candidate_count = 0
            elif isinstance(result, dict):
                status = result.get("status")
                candidate_count = result.get("candidates", 0)
            else:
                raise RuntimeError(
                    f"Unexpected check_board result: {result!r}"
                )

            if status not in counts:
                raise RuntimeError(
                    f"Unexpected check_board status: {status!r}"
                )

            if (
                not isinstance(candidate_count, int)
                or isinstance(candidate_count, bool)
                or candidate_count < 0
            ):
                raise RuntimeError(
                    f"Invalid candidate count: {candidate_count!r}"
                )

            if status == "eligible":
                total_candidates += candidate_count

                if args.delete:
                    active_ids = result.get("active_ids")

                    if status == "eligible" and not active_ids:
                        raise RuntimeError(
                            "Deletion blocked: missing validated active job IDs."
                        )

                    if status == "eligible":
                        with sqlite3.connect(database_path) as connection:
                            deleted = commit_closed_job_deletions(
                                connection,
                                board_token,
                                active_ids,
                            )
                        total_deleted += deleted
                        print(f"DELETED: {deleted} closed jobs")

            counts[status] += 1

        except Exception as error:
            counts["failed"] += 1
            print(f"FAILED {board_token}: {error}")

    print("\n" + "=" * 40)
    print(
        "GREENHOUSE CLEANUP SUMMARY"
        if args.delete
        else "GREENHOUSE CLEANUP DRY-RUN SUMMARY"
    )
    print("=" * 40)
    print(f"Boards attempted: {len(boards)}")
    print(f"Eligible boards: {counts['eligible']}")
    print(f"Blocked boards: {counts['blocked']}")
    print(f"Skipped boards: {counts['skipped']}")
    print(f"Failed boards: {counts['failed']}")
    print(f"Eligible job candidates: {total_candidates}")
    print(f"Jobs deleted: {total_deleted}")


if __name__ == "__main__":
    main()
