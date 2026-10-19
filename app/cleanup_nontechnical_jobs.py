import sqlite3

from app.job_filters import is_technical_role


def main():
    connection = sqlite3.connect("data/jobhunter.db")

    try:
        # Identify jobs that do not match our technical-role filter.
        jobs = connection.execute(
            "SELECT id, title FROM jobs"
        ).fetchall()

        nontechnical_ids = [
            job_id
            for job_id, title in jobs
            if not is_technical_role(title)
        ]

        # Exclude jobs with applications or Gemini analyses.
        protected_ids = {
            row[0]
            for row in connection.execute(
                "SELECT job_id FROM applications"
            )
        }

        protected_ids.update(
            row[0]
            for row in connection.execute(
                "SELECT job_id FROM job_match_analysis"
            )
        )

        deletion_ids = [
            job_id
            for job_id in nontechnical_ids
            if job_id not in protected_ids
        ]

        print(f"Nontechnical jobs: {len(nontechnical_ids):,}")
        print(f"Protected jobs: {len(nontechnical_ids) - len(deletion_ids):,}")
        print(f"Deletion candidates: {len(deletion_ids):,}")

        # Preview only. No deletion until explicitly enabled.
        # Delete only nontechnical jobs without applications or AI analyses.
        with connection:
            connection.executemany(
                """
                DELETE FROM jobs
                WHERE id = ?
                AND NOT EXISTS (
                    SELECT 1 FROM applications
                    WHERE applications.job_id = jobs.id
                )
                AND NOT EXISTS (
                    SELECT 1 FROM job_match_analysis
                    WHERE job_match_analysis.job_id = jobs.id
                )
                """,
                [(job_id,) for job_id in deletion_ids]
            )

        print(f"\nCleanup completed. Attempted deletions: {len(deletion_ids):,}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()