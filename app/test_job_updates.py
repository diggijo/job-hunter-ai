import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.database import add_job
from app.models import Job


def test_job_updates():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"

        original_connect = sqlite3.connect

        def test_connect(database, *args, **kwargs):
            return original_connect(db_path, *args, **kwargs)

        with patch("app.database.sqlite3.connect", side_effect=test_connect):
            connection = original_connect(db_path)

            connection.execute("""
                CREATE TABLE jobs (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    description TEXT,
                    url TEXT UNIQUE,
                    source TEXT
                )
            """)

            connection.execute("""
                CREATE TABLE job_match_analysis (
                    id INTEGER PRIMARY KEY,
                    candidate_id INTEGER,
                    job_id INTEGER,
                    analysis_json TEXT
                )
            """)

            connection.commit()
            connection.close()

            job = Job(
                title="Junior Software Engineer",
                company="Test Company",
                location="Dublin",
                description="Python required",
                url="https://example.com/test-job",
                source="Test"
            )

            assert add_job(job) == "Added"

            connection = original_connect(db_path)
            job_id = connection.execute(
                "SELECT id FROM jobs WHERE url = ?",
                (job.url,)
            ).fetchone()[0]

            connection.execute(
                """
                INSERT INTO job_match_analysis
                (candidate_id, job_id, analysis_json)
                VALUES (?, ?, ?)
                """,
                (1, job_id, "{}")
            )
            connection.commit()
            connection.close()

            assert add_job(job) == "Unchanged"

            connection = original_connect(db_path)
            cached_count = connection.execute(
                "SELECT COUNT(*) FROM job_match_analysis"
            ).fetchone()[0]
            connection.close()

            assert cached_count == 1, "Unchanged job should retain cache"

            updated_job = job.model_copy(
                update={"description": "Python and Docker required"}
            )

            assert add_job(updated_job) == "Updated"

            connection = original_connect(db_path)

            saved_description = connection.execute(
                "SELECT description FROM jobs WHERE id = ?",
                (job_id,)
            ).fetchone()[0]

            cached_count = connection.execute(
                "SELECT COUNT(*) FROM job_match_analysis"
            ).fetchone()[0]

            connection.close()

            assert saved_description == "Python and Docker required"
            assert cached_count == 0, "Updated job should invalidate cache"

            print("All job update tests passed!")


if __name__ == "__main__":
    test_job_updates()