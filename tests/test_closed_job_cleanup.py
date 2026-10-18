import pytest
import sqlite3
import subprocess
import sys

from app.check_closed_jobs import delete_closed_jobs

from types import SimpleNamespace
from unittest.mock import patch

from app.check_closed_jobs import get_valid_active_ids, commit_closed_job_deletions, check_board


def test_closed_job_cleanup():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed job', 'Greenhouse', 'testboard', '101'),
                (2, 'Applied job', 'Greenhouse', 'testboard', '102'),
                (3, 'Evaluated job', 'Greenhouse', 'testboard', '103'),
                (4, 'Active job', 'Greenhouse', 'testboard', '104'),
                (5, 'Other board', 'Greenhouse', 'otherboard', '105');

            INSERT INTO applications VALUES (2);
            INSERT INTO job_match_analysis VALUES (3);
        """)

        connection.commit()

        active_ids = {"104"}

        # Dry run must not delete anything.
        assert delete_closed_jobs(
            connection, "testboard", active_ids
        ) == 0

        assert connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0] == 5

        # Confirmed deletion must remove only job 1.
        assert delete_closed_jobs(
            connection, "testboard", active_ids, confirm=True
        ) == 1

        remaining = {
            row[0] for row in connection.execute(
                "SELECT id FROM jobs"
            )
        }
        assert remaining == {2, 3, 4, 5}

        # Roll back the deletion.
        connection.rollback()

        assert connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0] == 5

    finally:
        connection.close()


def test_deletion_requires_foreign_keys():
    connection = sqlite3.connect(":memory:")

    try:
        connection.execute("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            )
        """)

        connection.execute("""
            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            )
        """)

        connection.execute("""
            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            )
        """)

        connection.execute("""
            INSERT INTO jobs
            VALUES (1, 'Closed job', 'Greenhouse', 'testboard', '101')
        """)

        with pytest.raises(RuntimeError, match="Foreign-key enforcement"):
            delete_closed_jobs(
                connection,
                "testboard",
                active_ids=set(),
                confirm=True
            )

        assert connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0] == 1

    finally:
        connection.close()


def test_valid_greenhouse_job_ids():
    jobs = [
        SimpleNamespace(external_job_id="101"),
        SimpleNamespace(external_job_id="102"),
    ]

    assert get_valid_active_ids(jobs) == {"101", "102"}


def test_empty_greenhouse_response():
    assert get_valid_active_ids([]) is None


def test_missing_greenhouse_job_id():
    jobs = [
        SimpleNamespace(external_job_id="101"),
        SimpleNamespace(external_job_id=None),
    ]

    assert get_valid_active_ids(jobs) is None


def test_malformed_greenhouse_job_id():
    jobs = [
        SimpleNamespace(external_job_id="101"),
        SimpleNamespace(external_job_id="invalid"),
    ]

    assert get_valid_active_ids(jobs) is None


def test_duplicate_greenhouse_job_ids():
    jobs = [
        SimpleNamespace(external_job_id="101"),
        SimpleNamespace(external_job_id="101"),
    ]

    assert get_valid_active_ids(jobs) is None


def test_committed_cleanup_preserves_protected_jobs():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Applied', 'Greenhouse', 'testboard', '102'),
                (3, 'Evaluated', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Other board', 'Greenhouse', 'otherboard', '105'),
                (6, 'Another active job', 'Greenhouse', 'testboard', '106');        

            INSERT INTO applications VALUES (2);
            INSERT INTO job_match_analysis VALUES (3);
        """)

        connection.commit()

        with pytest.raises(
            RuntimeError,
            match="more than 20%"
        ):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {"104", "106"}
            )

        assert not connection.in_transaction

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {1, 2, 3, 4, 5, 6}

        assert connection.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()[0] == 1

        assert connection.execute(
            "SELECT COUNT(*) FROM job_match_analysis"
        ).fetchone()[0] == 1

    finally:
        connection.close()


def test_cleanup_blocks_large_deletions():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Active', 'Greenhouse', 'testboard', '102'),
                (3, 'Active', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104');
        """)

        connection.commit()

        with pytest.raises(
            RuntimeError,
            match="fewer than 5 tracked jobs"
        ):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {"102", "103", "104"}
            )

        assert connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0] == 4

    finally:
        connection.close()


def test_cleanup_rejects_empty_active_ids():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101');
        """)

        connection.commit()

        with pytest.raises(
            RuntimeError,
            match="active job IDs are empty or invalid"
        ):
            commit_closed_job_deletions(
                connection,
                "testboard",
                set()
            )

        assert connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0] == 1

    finally:
        connection.close()


@pytest.mark.parametrize("board_token", [None, "", "   ", 123])
def test_cleanup_rejects_invalid_board_token(board_token):
    connection = sqlite3.connect(":memory:")

    try:
        with pytest.raises(
            RuntimeError,
            match="board token is missing or invalid"
        ):
            commit_closed_job_deletions(
                connection,
                board_token,
                {"101"}
            )

    finally:
        connection.close()


def test_cleanup_rejects_board_with_no_stored_jobs():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );
        """)

        with pytest.raises(
            RuntimeError,
            match="no tracked jobs found"
        ):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {"101"}
            )

        assert connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0] == 0

    finally:
        connection.close()


def test_failed_greenhouse_request_skips_cleanup(capsys):
    def fake_fetch(board_token):
        assert board_token == "testboard"
        return None

    with patch(
        "app.check_closed_jobs.sqlite3.connect",
        side_effect=AssertionError(
            "Database must not be opened after a failed API response"
        )
    ):
        check_board("testboard", fetch_jobs=fake_fetch)

    output = capsys.readouterr().out

    assert "Board unavailable. Skipping." in output


def test_empty_greenhouse_response_skips_cleanup(capsys):
    def fake_fetch(board_token):
        assert board_token == "testboard"
        return []

    with patch(
        "app.check_closed_jobs.sqlite3.connect",
        side_effect=AssertionError(
            "Database must not be opened after an empty API response"
        )
    ):
        check_board("testboard", fetch_jobs=fake_fetch)

    output = capsys.readouterr().out

    assert "Board returned no jobs. Skipping for safety." in output


@pytest.mark.parametrize(
    "job_ids",
    [
        ["101", None],
        ["101", "invalid"],
        ["101", "101"],
    ]
)
def test_invalid_greenhouse_response_skips_cleanup(job_ids, capsys):
    jobs = [
        SimpleNamespace(external_job_id=job_id)
        for job_id in job_ids
    ]

    with patch(
        "app.check_closed_jobs.sqlite3.connect",
        side_effect=AssertionError(
            "Database must not open for invalid API responses"
        )
    ):
        check_board(
            "testboard",
            fetch_jobs=lambda board_token: jobs
        )

    output = capsys.readouterr().out

    assert "Invalid, missing, or duplicate job IDs." in output


def test_valid_greenhouse_response_runs_dry_run(capsys):
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER,
                status TEXT
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER
            );

            INSERT INTO jobs VALUES
                (1, 'Closed job', 'Greenhouse', 'testboard', '101'),
                (2, 'Active job', 'Greenhouse', 'testboard', '102'),
                (3, 'Active job 2', 'Greenhouse', 'testboard', '103'),
                (4, 'Active job 3', 'Greenhouse', 'testboard', '104'),
                (5, 'Active job 4', 'Greenhouse', 'testboard', '105');
        """)

        connection.commit()

        jobs = [
            SimpleNamespace(external_job_id=str(job_id))
            for job_id in range(102, 106)
        ]

        changes_before = connection.total_changes
        changes_after = []

        original_close = connection.close

        class ConnectionWrapper:
            def __init__(self, wrapped):
                self.wrapped = wrapped

            def __getattr__(self, name):
                return getattr(self.wrapped, name)

            def close(self):
                changes_after.append(self.wrapped.total_changes)
                original_close()

        with patch(
            "app.check_closed_jobs.sqlite3.connect",
            return_value=ConnectionWrapper(connection)
        ):
            check_board(
                "testboard",
                fetch_jobs=lambda board_token: jobs
            )

        assert changes_after == [changes_before]

        output = capsys.readouterr().out

        assert "Currently active jobs: 4" in output
        assert "Potentially closed: 1" in output
        assert "Eligible cleanup candidates: 1" in output
        assert "DRY RUN: 1 jobs eligible for deletion." in output
        with sqlite3.connect(":memory:") as verification:
            pass

    finally:
        connection.close()


def test_successful_cleanup_preserves_protected_jobs():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Applied', 'Greenhouse', 'testboard', '102'),
                (3, 'Evaluated', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105'),
                (6, 'Active', 'Greenhouse', 'testboard', '106');

            INSERT INTO applications VALUES (2);
            INSERT INTO job_match_analysis VALUES (3);
        """)

        connection.commit()

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            {"102", "103", "104", "105", "106"}
        )

        assert deleted == 1

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {2, 3, 4, 5, 6}

        assert connection.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()[0] == 1

        assert connection.execute(
            "SELECT COUNT(*) FROM job_match_analysis"
        ).fetchone()[0] == 1

    finally:
        connection.close()


def test_cleanup_allows_exactly_twenty_percent():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Active', 'Greenhouse', 'testboard', '102'),
                (3, 'Active', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105');
        """)

        connection.commit()

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            {"102", "103", "104", "105"}
        )

        assert deleted == 1

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {2, 3, 4, 5}

    finally:
        connection.close()


def test_protected_missing_jobs_count_toward_safety_limit():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Applied', 'Greenhouse', 'testboard', '102'),
                (3, 'Evaluated', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105'),
                (6, 'Active', 'Greenhouse', 'testboard', '106');

            INSERT INTO applications VALUES (2);
            INSERT INTO job_match_analysis VALUES (3);
        """)

        connection.commit()

        with pytest.raises(RuntimeError, match="more than 20%"):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {"104", "105", "106"}
            )

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {1, 2, 3, 4, 5, 6}

    finally:
        connection.close()


def test_cleanup_does_not_delete_other_board_jobs():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Active', 'Greenhouse', 'testboard', '102'),
                (3, 'Active', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105'),
                (6, 'Other company', 'Greenhouse', 'otherboard', '101');
        """)

        connection.commit()

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            {"102", "103", "104", "105"}
        )

        assert deleted == 1

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {2, 3, 4, 5, 6}

    finally:
        connection.close()


def test_closed_protected_jobs_survive_successful_cleanup():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Applied closed', 'Greenhouse', 'testboard', '102'),
                (3, 'Evaluated closed', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105'),
                (6, 'Active', 'Greenhouse', 'testboard', '106'),
                (7, 'Active', 'Greenhouse', 'testboard', '107'),
                (8, 'Active', 'Greenhouse', 'testboard', '108'),
                (9, 'Active', 'Greenhouse', 'testboard', '109'),
                (10, 'Active', 'Greenhouse', 'testboard', '110'),
                (11, 'Active', 'Greenhouse', 'testboard', '111'),
                (12, 'Active', 'Greenhouse', 'testboard', '112'),
                (13, 'Active', 'Greenhouse', 'testboard', '113'),
                (14, 'Active', 'Greenhouse', 'testboard', '114'),
                (15, 'Active', 'Greenhouse', 'testboard', '115');

            INSERT INTO applications VALUES (2);
            INSERT INTO job_match_analysis VALUES (3);
        """)

        connection.commit()

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            {str(job_id) for job_id in range(104, 116)}
        )

        assert deleted == 1

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == set(range(2, 16))

        assert connection.execute(
            "SELECT job_id FROM applications"
        ).fetchone()[0] == 2

        assert connection.execute(
            "SELECT job_id FROM job_match_analysis"
        ).fetchone()[0] == 3

    finally:
        connection.close()


def test_cleanup_preserves_not_interested_jobs():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id),
                status TEXT
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Not interested', 'Greenhouse', 'testboard', '102'),
                (3, 'Active', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105'),
                (6, 'Active', 'Greenhouse', 'testboard', '106'),
                (7, 'Active', 'Greenhouse', 'testboard', '107'),
                (8, 'Active', 'Greenhouse', 'testboard', '108'),
                (9, 'Active', 'Greenhouse', 'testboard', '109'),
                (10, 'Active', 'Greenhouse', 'testboard', '110');

            INSERT INTO applications VALUES (2, 'not_interested');
        """)

        connection.commit()

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            {str(job_id) for job_id in range(103, 111)}
        )

        assert deleted == 1

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == set(range(2, 11))

        assert connection.execute(
            "SELECT status FROM applications WHERE job_id = 2"
        ).fetchone()[0] == "not_interested"

    finally:
        connection.close()


def test_cleanup_preserves_untracked_jobs():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Active', 'Greenhouse', 'testboard', '102'),
                (3, 'Active', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105'),
                (6, 'Missing board', 'Greenhouse', NULL, '106'),
                (7, 'Missing job ID', 'Greenhouse', 'testboard', NULL),
                (8, 'Fully untracked', 'Greenhouse', NULL, NULL);
        """)

        connection.commit()

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            {"102", "103", "104", "105"}
        )

        assert deleted == 1

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {2, 3, 4, 5, 6, 7, 8}

    finally:
        connection.close()


def test_cleanup_preserves_other_sources():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Active', 'Greenhouse', 'testboard', '102'),
                (3, 'Active', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105'),
                (6, 'Other source', 'Lever', 'testboard', '101');
        """)

        connection.commit()

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            {"102", "103", "104", "105"}
        )

        assert deleted == 1

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {2, 3, 4, 5, 6}

    finally:
        connection.close()


def test_cleanup_rejects_existing_transaction():
    connection = sqlite3.connect(":memory:")

    try:
        connection.execute("BEGIN")

        with pytest.raises(
            RuntimeError,
            match="already has an active transaction"
        ):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {"101"}
            )

        assert connection.in_transaction

    finally:
        connection.rollback()
        connection.close()


def test_cleanup_rolls_back_if_second_deletion_fails():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER REFERENCES jobs(id)
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER REFERENCES jobs(id)
            );

            INSERT INTO jobs VALUES
                (1, 'Closed 1', 'Greenhouse', 'testboard', '101'),
                (2, 'Closed 2', 'Greenhouse', 'testboard', '102'),
                (3, 'Active', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105'),
                (6, 'Active', 'Greenhouse', 'testboard', '106'),
                (7, 'Active', 'Greenhouse', 'testboard', '107'),
                (8, 'Active', 'Greenhouse', 'testboard', '108'),
                (9, 'Active', 'Greenhouse', 'testboard', '109'),
                (10, 'Active', 'Greenhouse', 'testboard', '110');

            CREATE TRIGGER block_second_deletion
            BEFORE DELETE ON jobs
            WHEN OLD.id = 2
            BEGIN
                SELECT RAISE(ABORT, 'Simulated deletion failure');
            END;
        """)

        connection.commit()

        with pytest.raises(
            sqlite3.IntegrityError,
            match="Simulated deletion failure"
        ):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {str(job_id) for job_id in range(103, 111)}
            )

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == set(range(1, 11))
        assert not connection.in_transaction

    finally:
        connection.close()


def test_delete_command_is_disabled():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "app.check_closed_jobs", "--delete"],
        capture_output=True,
        text=True
    )

    assert result.returncode != 0
    assert "Deletion is not enabled yet" in result.stderr


def test_delete_command_with_board_token_is_disabled():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.check_closed_jobs",
            "vaxcyte",
            "--delete"
        ],
        capture_output=True,
        text=True
    )

    assert result.returncode != 0
    assert "Usage: python -m app.check_closed_jobs BOARD_TOKEN" in result.stdout


def test_safety_limit_blocks_before_transaction():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER
            );

            INSERT INTO jobs VALUES
                (1, 'Greenhouse', 'testboard', '101'),
                (2, 'Greenhouse', 'testboard', '102'),
                (3, 'Greenhouse', 'testboard', '103'),
                (4, 'Greenhouse', 'testboard', '104'),
                (5, 'Greenhouse', 'testboard', '105');
        """)

        connection.commit()

        with pytest.raises(RuntimeError, match="more than 20%"):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {"103", "104", "105"}
            )

        assert not connection.in_transaction
        assert connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0] == 5

    finally:
        connection.close()


def test_cleanup_blocks_board_with_four_jobs():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER
            );

            INSERT INTO jobs VALUES
                (1, 'Greenhouse', 'testboard', '101'),
                (2, 'Greenhouse', 'testboard', '102'),
                (3, 'Greenhouse', 'testboard', '103'),
                (4, 'Greenhouse', 'testboard', '104');
        """)

        connection.commit()

        with pytest.raises(
            RuntimeError,
            match="fewer than 5 tracked jobs"
        ):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {"101", "102", "103", "104"}
            )

        assert not connection.in_transaction

        assert connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0] == 4

    finally:
        connection.close()


def test_cleanup_allows_five_job_board():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER
            );

            INSERT INTO jobs VALUES
                (1, 'Closed', 'Greenhouse', 'testboard', '101'),
                (2, 'Active', 'Greenhouse', 'testboard', '102'),
                (3, 'Active', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105');
        """)

        connection.commit()

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            {"102", "103", "104", "105"}
        )

        assert deleted == 1

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {2, 3, 4, 5}

    finally:
        connection.close()


def test_five_job_board_blocks_two_missing_jobs():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER
            );

            INSERT INTO jobs VALUES
                (1, 'Greenhouse', 'testboard', '101'),
                (2, 'Greenhouse', 'testboard', '102'),
                (3, 'Greenhouse', 'testboard', '103'),
                (4, 'Greenhouse', 'testboard', '104'),
                (5, 'Greenhouse', 'testboard', '105');
        """)

        connection.commit()

        with pytest.raises(RuntimeError, match="more than 20%"):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {"103", "104", "105"}
            )

        assert not connection.in_transaction

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {1, 2, 3, 4, 5}

    finally:
        connection.close()


def test_cleanup_allows_three_closed_jobs_out_of_fifty():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER
            );
        """)

        connection.executemany(
            """
            INSERT INTO jobs
                (id, title, source, source_board_id, external_job_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (i, f"Job {i}", "Greenhouse", "testboard", str(i))
                for i in range(1, 51)
            ]
        )

        connection.commit()

        active_ids = {str(i) for i in range(4, 51)}

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            active_ids
        )

        assert deleted == 3

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == set(range(4, 51))

    finally:
        connection.close()


def test_cleanup_with_no_closed_jobs():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER
            );

            INSERT INTO jobs VALUES
                (1, 'Active', 'Greenhouse', 'testboard', '101'),
                (2, 'Active', 'Greenhouse', 'testboard', '102'),
                (3, 'Active', 'Greenhouse', 'testboard', '103'),
                (4, 'Active', 'Greenhouse', 'testboard', '104'),
                (5, 'Active', 'Greenhouse', 'testboard', '105');
        """)

        connection.commit()

        changes_before = connection.total_changes

        deleted = commit_closed_job_deletions(
            connection,
            "testboard",
            {"101", "102", "103", "104", "105"}
        )

        assert deleted == 0
        assert connection.total_changes == changes_before

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == {1, 2, 3, 4, 5}

    finally:
        connection.close()


def test_cleanup_rolls_back_when_twenty_percent_limit_exceeded():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER
            );
        """)

        connection.executemany(
            """
            INSERT INTO jobs
                (id, source, source_board_id, external_job_id)
            VALUES (?, 'Greenhouse', 'testboard', ?)
            """,
            [(i, str(i)) for i in range(1, 11)]
        )

        connection.commit()

        with pytest.raises(RuntimeError, match="more than 20%"):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {str(i) for i in range(4, 11)}
            )

        assert not connection.in_transaction

        remaining = {
            row[0]
            for row in connection.execute("SELECT id FROM jobs")
        }

        assert remaining == set(range(1, 11))

    finally:
        connection.close()


def test_cleanup_rolls_back_when_board_too_small():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                source TEXT,
                source_board_id TEXT,
                external_job_id TEXT
            );

            CREATE TABLE applications (
                job_id INTEGER
            );

            CREATE TABLE job_match_analysis (
                job_id INTEGER
            );

            INSERT INTO jobs VALUES
                (1, 'Greenhouse', 'testboard', '101'),
                (2, 'Greenhouse', 'testboard', '102'),
                (3, 'Greenhouse', 'testboard', '103'),
                (4, 'Greenhouse', 'testboard', '104');
        """)

        connection.commit()

        with pytest.raises(
            RuntimeError,
            match="fewer than 5 tracked jobs"
        ):
            commit_closed_job_deletions(
                connection,
                "testboard",
                {"101", "102", "103", "104"}
            )

        assert not connection.in_transaction

        assert connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0] == 4

    finally:
        connection.close()
