import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from app.database import add_job, initialize_database
from app.models import Job


class BoardTokenTests(unittest.TestCase):
    def test_board_token_preserves_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "test.db"
            real_connect = sqlite3.connect

            def test_connect(*args, **kwargs):
                return real_connect(db_path, **kwargs)

            with patch("app.database.sqlite3.connect", side_effect=test_connect):
                initialize_database()

                job = Job(
                    title="Software Engineer",
                    company="Test Company",
                    location="London",
                    description="Python developer",
                    url="https://example.com/test-job",
                    source="Greenhouse",
                )

                self.assertEqual(add_job(job), "Added")

                with closing(real_connect(db_path)) as connection:
                    job_id = connection.execute(
                        "SELECT id FROM jobs WHERE url = ?", (job.url,)
                    ).fetchone()[0]

                    connection.execute(
                        "INSERT INTO job_match_analysis "
                        "(candidate_id, job_id, analysis_json) VALUES (?, ?, ?)",
                        (1, job_id, '{"score": 90}'),
                    )

                    connection.commit()

                job.source_board_id = "testcompany"
                job.external_job_id = "1234567"
                self.assertEqual(add_job(job), "Updated")

                with closing(real_connect(db_path)) as connection:
                    identifiers = connection.execute(
                        "SELECT source_board_id, external_job_id FROM jobs WHERE id = ?",
                        (job_id,)
                    ).fetchone()

                    analysis_count = connection.execute(
                        "SELECT COUNT(*) FROM job_match_analysis WHERE job_id = ?",
                        (job_id,),
                    ).fetchone()[0]

                self.assertEqual(identifiers, ("testcompany", "1234567"))
                self.assertEqual(analysis_count, 1)

                job.source_board_id = None
                job.external_job_id = None
                self.assertEqual(add_job(job), "Unchanged")

                job.description = "Updated job description"
                self.assertEqual(add_job(job), "Updated")

                with closing(real_connect(db_path)) as connection:
                    analysis_count = connection.execute(
                        "SELECT COUNT(*) FROM job_match_analysis WHERE job_id = ?",
                        (job_id,),
                    ).fetchone()[0]

                self.assertEqual(analysis_count, 0)


if __name__ == "__main__":
    unittest.main()
