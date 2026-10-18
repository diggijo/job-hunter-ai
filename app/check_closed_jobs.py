import sqlite3
import sys

from app.collectors.greenhouse import get_greenhouse_jobs


def get_cleanup_candidates(connection, board_token, active_ids):
    rows = connection.execute(
        """
        SELECT j.id, j.title, j.external_job_id
        FROM jobs j
        WHERE j.source = 'Greenhouse'
          AND j.source_board_id = ?
          AND j.external_job_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM applications a
              WHERE a.job_id = j.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM job_match_analysis m
              WHERE m.job_id = j.id
          )
        """,
        (board_token,)
    ).fetchall()

    return [
        row for row in rows
        if row[2] not in active_ids
    ]


def delete_closed_jobs(connection, board_token, active_ids, confirm=False):
    candidates = get_cleanup_candidates(
        connection, board_token, active_ids
    )

    if not confirm:
        print(f"DRY RUN: {len(candidates)} jobs eligible for deletion.")
        return 0

    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError(
            "Foreign-key enforcement must be enabled before deletion."
        )

    deleted = 0

    for job_id, title, external_id in candidates:
        cursor = connection.execute(
            """
            DELETE FROM jobs
            WHERE id = ?
              AND source = 'Greenhouse'
              AND source_board_id = ?
              AND external_job_id = ?
              AND NOT EXISTS (
                  SELECT 1 FROM applications
                  WHERE job_id = jobs.id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM job_match_analysis
                  WHERE job_id = jobs.id
              )
            """,
            (job_id, board_token, external_id)
        )
        deleted += cursor.rowcount

    print(f"Deleted {deleted} closed jobs.")
    return deleted


def get_valid_active_ids(jobs):
    if not jobs:
        return None

    ids = [job.external_job_id for job in jobs]

    if any(
        not isinstance(job_id, str) or not job_id.isdigit()
        for job_id in ids
    ):
        return None

    if len(set(ids)) != len(ids):
        return None

    return set(ids)


def validate_cleanup_threshold(stored_count, missing_count):
    if stored_count == 0:
        raise RuntimeError(
            "Deletion blocked: no tracked jobs found for this board."
        )

    if stored_count < 5:
        raise RuntimeError(
            "Deletion blocked: fewer than 5 tracked jobs on this board."
        )

    if missing_count / stored_count > 0.20:
        raise RuntimeError(
            "Deletion blocked: more than 20% of stored jobs are missing from Greenhouse."
        )


def commit_closed_job_deletions(connection, board_token, active_ids):
    if connection.in_transaction:
        raise RuntimeError("Connection already has an active transaction.")

    if (
        not isinstance(board_token, str)
        or not board_token.strip()
    ):
        raise RuntimeError(
            "Deletion blocked: board token is missing or invalid."
        )

    if (
        not isinstance(active_ids, set)
        or not active_ids
        or any(
            not isinstance(job_id, str) or not job_id.isdigit()
            for job_id in active_ids
        )
    ):
        raise RuntimeError(
            "Deletion blocked: active job IDs are empty or invalid."
        )

    # Enable foreign-key enforcement before starting the transaction.
    connection.execute("PRAGMA foreign_keys = ON")

    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("Could not enable foreign-key enforcement.")

    try:
        # Lock the database for writing before checking stored jobs.
        connection.execute("BEGIN IMMEDIATE")

        stored_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM jobs
            WHERE source = 'Greenhouse'
              AND source_board_id = ?
              AND external_job_id IS NOT NULL
            """,
            (board_token,)
        ).fetchone()[0]

        stored_ids = connection.execute(
            """
            SELECT external_job_id
            FROM jobs
            WHERE source = 'Greenhouse'
              AND source_board_id = ?
              AND external_job_id IS NOT NULL
            """,
            (board_token,)
        ).fetchall()

        missing_count = sum(
            1 for (external_id,) in stored_ids
            if external_id not in active_ids
        )

        validate_cleanup_threshold(stored_count, missing_count)

        if missing_count / stored_count > 0.20:
            raise RuntimeError(
                "Deletion blocked: more than 20% of stored jobs are missing from Greenhouse."
            )

        # Delete only eligible closed jobs.
        deleted = delete_closed_jobs(
            connection,
            board_token,
            active_ids,
            confirm=True
        )

        connection.commit()
        return deleted

    except Exception:
        connection.rollback()
        raise


def check_board(board_token, fetch_jobs=None):
    if fetch_jobs is None:
        fetch_jobs = get_greenhouse_jobs

    jobs = fetch_jobs(board_token)

    if jobs is None:
        print("Board unavailable. Skipping.")
        return {"status": "skipped", "candidates": 0}

    if not jobs:
        print("Board returned no jobs. Skipping for safety.")
        return {"status": "skipped", "candidates": 0}

    active_ids = get_valid_active_ids(jobs)

    if active_ids is None:
        print("Invalid, missing, or duplicate job IDs. Skipping for safety.")
        return {"status": "skipped", "candidates": 0}

    connection = sqlite3.connect(
        "file:data/jobhunter.db?mode=ro",
        uri=True,
    )

    try:
        stored_jobs = connection.execute(
            """
            SELECT j.id, j.title, j.external_job_id,
                   a.status
            FROM jobs j
            LEFT JOIN applications a ON a.job_id = j.id
            WHERE j.source = 'Greenhouse'
              AND j.source_board_id = ?
              AND j.external_job_id IS NOT NULL
            """,
            (board_token,)
        ).fetchall()

        potentially_closed = [
            job for job in stored_jobs
            if job[2] not in active_ids
        ]

        eligible = get_cleanup_candidates(
            connection, board_token, active_ids
        )

        eligible_ids = {job[0] for job in eligible}

        protected = [
            job for job in potentially_closed
            if job[0] not in eligible_ids
        ]

        print(f"Board: {board_token}")
        print(f"Currently active jobs: {len(active_ids)}")
        print(f"Stored jobs: {len(stored_jobs)}")
        print(f"Potentially closed: {len(potentially_closed)}")
        print(f"Protected jobs (applications or Gemini): {len(protected)}")
        print(f"Eligible cleanup candidates: {len(eligible)}")

        for job_id, title, external_id in eligible[:10]:
            print(f"  {job_id}: {title} ({external_id})")

        stored_count = len(stored_jobs)
        missing_count = len(potentially_closed)

        try:
            validate_cleanup_threshold(stored_count, missing_count)
        except RuntimeError as error:
            print(f"BLOCKED: {error}")
            return {"status": "blocked", "candidates": 0}

        delete_closed_jobs(
            connection,
            board_token,
            active_ids,
            confirm=False
        )
        return {
            "status": "eligible",
            "candidates": len(eligible),
            "active_ids": active_ids,
        }

    finally:
        connection.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.check_closed_jobs BOARD_TOKEN")
        sys.exit(1)

    if "--delete" in sys.argv:
        raise RuntimeError(
            "Deletion is not enabled yet. Dry-run mode only."
        )

    check_board(sys.argv[1])
