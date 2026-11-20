
import argparse
import sqlite3
import time

import httpx

from app.collectors.lever import build_lever_description
from app.database import DB_PATH


def repair_lever_descriptions(apply_changes=False):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        boards = connection.execute("""
            SELECT DISTINCT source_board_id
            FROM jobs
            WHERE source = 'Lever'
              AND LENGTH(COALESCE(description, '')) < 500
              AND source_board_id IS NOT NULL
        """).fetchall()

        total_improved = 0
        total_updated = 0
        failed_boards = []

        print(f"Boards to inspect: {len(boards)}", flush=True)

        with httpx.Client(timeout=20.0) as client:
            for index, board_row in enumerate(boards, start=1):
                board = board_row["source_board_id"]

                print(
                    f"[{index}/{len(boards)}] {board}",
                    flush=True,
                )

                try:
                    response = client.get(
                        f"https://api.lever.co/v0/postings/{board}",
                        params={"mode": "json"},
                    )
                    response.raise_for_status()
                    postings = response.json()

                    if not isinstance(postings, list):
                        raise ValueError("Invalid API response")

                except (httpx.HTTPError, ValueError) as error:
                    print(f"  Failed: {error}", flush=True)
                    failed_boards.append(board)
                    continue

                posting_lookup = {
                    str(posting["id"]): posting
                    for posting in postings
                }

                jobs = connection.execute("""
                    SELECT id, external_job_id, description
                    FROM jobs
                    WHERE source = 'Lever'
                      AND source_board_id = ?
                      AND LENGTH(COALESCE(description, '')) < 500
                """, (board,)).fetchall()

                board_improved = 0

                for job in jobs:
                    posting = posting_lookup.get(
                        job["external_job_id"]
                    )

                    if posting is None:
                        continue

                    new_description = build_lever_description(posting)
                    old_description = job["description"] or ""

                    if len(new_description) <= len(old_description):
                        continue

                    total_improved += 1
                    board_improved += 1

                    if apply_changes:
                        connection.execute("""
                            UPDATE jobs
                            SET description = ?
                            WHERE id = ?
                        """, (new_description, job["id"]))

                        connection.execute("""
                            DELETE FROM job_match_analysis
                            WHERE job_id = ?
                        """, (job["id"],))

                        connection.commit()
                        total_updated += 1

                print(
                    f"  Improved descriptions: {board_improved}",
                    flush=True,
                )

                time.sleep(0.2)

        print("\nRepair summary")
        print(f"Descriptions improved: {total_improved}")
        print(f"Database records updated: {total_updated}")
        print(f"Failed boards: {len(failed_boards)}")

        if failed_boards:
            print("Failed board names:")
            for board in failed_boards:
                print(f"  {board}")

    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply database changes; otherwise dry-run only",
    )
    args = parser.parse_args()

    repair_lever_descriptions(apply_changes=args.apply)
