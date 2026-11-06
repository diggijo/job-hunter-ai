import sqlite3
DB_PATH = "data/jobhunter.db"
from app.config import JOB_MATCH_CACHE_VERSION
from app.models import Job, CandidateAnalysis, CandidateProfile, JobMatchAnalysis
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError


def initialize_database():
    connection = sqlite3.connect(DB_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS candidate_profile (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS preferred_roles (
            id INTEGER PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidate_profile (id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS preferred_locations (
            id INTEGER PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            location TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidate_profile (id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            source TEXT NOT NULL,
            first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            source_board_id TEXT,
            external_job_id TEXT
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS greenhouse_boards (
            id INTEGER PRIMARY KEY,
            board_token TEXT NOT NULL UNIQUE,
            company_name TEXT,
            discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS ashby_boards (
            board_token TEXT PRIMARY KEY,
            company_name TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS candidate_analysis (
            id INTEGER PRIMARY KEY,
            candidate_id INTEGER NOT NULL UNIQUE,
            analysis_json TEXT NOT NULL,
            FOREIGN KEY (candidate_id)
                REFERENCES candidate_profile (id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS job_match_analysis (
            id INTEGER PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            analysis_json TEXT NOT NULL,
            UNIQUE(candidate_id, job_id),
            FOREIGN KEY (candidate_id)
                REFERENCES candidate_profile (id),
            FOREIGN KEY (job_id)
                REFERENCES jobs (id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS ai_api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            request_date TEXT NOT NULL,
            request_count INTEGER NOT NULL DEFAULT 0,
            UNIQUE(model, request_date)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS ai_request_timing (
            model TEXT PRIMARY KEY,
            last_request_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS ai_evaluation_queue (
            job_id INTEGER PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            last_error TEXT,
            failed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (candidate_id) REFERENCES candidate_profile(id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'not_applied',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    columns = connection.execute(
        "PRAGMA table_info(job_match_analysis)"
    ).fetchall()

    column_names = [column[1] for column in columns]

    if "cache_version" not in column_names:
        connection.execute("""
            ALTER TABLE job_match_analysis
            ADD COLUMN cache_version INTEGER NOT NULL DEFAULT 1
        """)

    connection.commit()
    connection.close()


def get_candidate_profile():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    candidate = connection.execute(
        "SELECT id, name FROM candidate_profile LIMIT 1"
    ).fetchone()

    roles = connection.execute(
        "SELECT role FROM preferred_roles WHERE candidate_id = ?",
        (candidate["id"],)
    ).fetchall()

    locations = connection.execute(
        "SELECT location FROM preferred_locations WHERE candidate_id = ?",
        (candidate["id"],)
    ).fetchall()

    connection.close()

    return {
        "name": candidate["name"],
        "preferred_roles": [row["role"] for row in roles],
        "preferred_locations": [row["location"] for row in locations]
    }


def add_job(job: Job):
    connection = sqlite3.connect(DB_PATH)

    try:
        existing_job = connection.execute(
            """
            SELECT id, title, company, location, description, source,
                   source_board_id, external_job_id
            FROM jobs
            WHERE url = ?
            """,
            (job.url,)
        ).fetchone()

        if existing_job is None:
            connection.execute(
                """
                INSERT INTO jobs (
                    title, company, location, description, url, source,
                    first_seen_at, source_board_id, external_job_id
                )
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                """,
                (
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.url,
                    job.source,
                    job.source_board_id,
                    job.external_job_id
                )
            )

            connection.commit()
            return "Added"

        job_id = existing_job[0]

        new_details = (
            job.title,
            job.company,
            job.location,
            job.description,
            job.source,
            job.source_board_id if job.source_board_id is not None else existing_job[6],
            job.external_job_id if job.external_job_id is not None else existing_job[7]
        )

        if existing_job[1:] == new_details:
            return "Unchanged"

        details_changed = existing_job[1:6] != new_details[:5]

        connection.execute(
            """
            UPDATE jobs
            SET title = ?,
                company = ?,
                location = ?,
                description = ?,
                source = ?,
                source_board_id = ?,
                external_job_id = ?
            WHERE id = ?
            """,
            (*new_details, job_id)
        )

        if details_changed:
            connection.execute(
                "DELETE FROM job_match_analysis WHERE job_id = ?",
                (job_id,)
            )

        connection.commit()
        return "Updated"

    finally:
        connection.close()


def invalidate_job_match_cache(job_id: int):
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute(
            "DELETE FROM job_match_analysis WHERE job_id = ?",
            (job_id,)
        )
        connection.commit()

    finally:
        connection.close()


def get_jobs():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    results = connection.execute(
        """
        SELECT id, title, company, location, description, url, source, first_seen_at
        FROM jobs
        """
    ).fetchall()

    connection.close()

    return results


def get_candidate_analysis(candidate_id: int) -> CandidateAnalysis | None:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.execute("""
            SELECT analysis_json
            FROM candidate_analysis
            WHERE candidate_id = ?
        """, (candidate_id,))

        row = cursor.fetchone()

        if row is None:
            return None

        try:
            return CandidateAnalysis.model_validate_json(
                row["analysis_json"]
            )
        except ValidationError:
            return None

    finally:
        connection.close()


def save_candidate_analysis(candidate_id: int, analysis: CandidateAnalysis):
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("""
            INSERT INTO candidate_analysis (
                candidate_id,
                analysis_json
            )
            VALUES (?, ?)
            ON CONFLICT(candidate_id)
            DO UPDATE SET
                analysis_json = excluded.analysis_json
        """, (
            candidate_id,
            analysis.model_dump_json()
        ))

        connection.commit()

    finally:
        connection.close()


def save_job_match_analysis(candidate_id: int, job_id: int, analysis: JobMatchAnalysis):

    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("""
            INSERT INTO job_match_analysis (
                candidate_id,
                job_id,
                analysis_json,
                cache_version
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(candidate_id, job_id)
            DO UPDATE SET
                analysis_json = excluded.analysis_json,
                cache_version = excluded.cache_version
        """, (
            candidate_id,
            job_id,
            analysis.model_dump_json(),
            JOB_MATCH_CACHE_VERSION
        ))

        connection.commit()

    finally:
        connection.close()


def get_job_match_analysis(candidate_id: int, job_id: int) -> JobMatchAnalysis | None:

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.execute("""
            SELECT analysis_json, cache_version
            FROM job_match_analysis
            WHERE candidate_id = ?
            AND job_id = ?
        """, (candidate_id, job_id))

        row = cursor.fetchone()

        if row is None:
            return None

        if row["cache_version"] != JOB_MATCH_CACHE_VERSION:
            return None

        try:
            return JobMatchAnalysis.model_validate_json(
                row["analysis_json"]
            )
        except ValidationError:
            return None

    finally:
        connection.close()


def add_greenhouse_board(board_token: str, company_name: str = None):
    connection = sqlite3.connect(DB_PATH)

    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO greenhouse_boards
        (board_token, company_name)
        VALUES (?, ?)
        """,
        (board_token, company_name)
    )

    connection.commit()

    added = cursor.rowcount > 0

    connection.close()

    return added


def get_greenhouse_boards():
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute(
        """
        SELECT board_token
        FROM greenhouse_boards
        ORDER BY board_token
        """
    ).fetchall()

    connection.close()

    return [row[0] for row in rows]


def add_ashby_board(board_token: str, company_name: str):
    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO ashby_boards
            (board_token, company_name)
            VALUES (?, ?)
            """,
            (board_token, company_name),
        )

        connection.commit()
        return cursor.rowcount > 0

    finally:
        connection.close()


def get_ashby_boards():
    connection = sqlite3.connect(DB_PATH)

    try:
        rows = connection.execute(
            """
            SELECT board_token, company_name
            FROM ashby_boards
            ORDER BY board_token
            """
        ).fetchall()

        return rows

    finally:
        connection.close()


def get_daily_ai_usage(model: str) -> int:
    # Gemini daily quotas reset at midnight Pacific Time.
    # This is 08:00 or 09:00 in Ireland depending on DST.
    pacific = timezone(timedelta(hours=-8))
    # Use America/Los_Angeles to handle daylight saving time.
    from zoneinfo import ZoneInfo

    request_date = datetime.now(
        ZoneInfo("America/Los_Angeles")
    ).date().isoformat()

    connection = sqlite3.connect(DB_PATH)

    try:
        row = connection.execute(
            """
            SELECT request_count
            FROM ai_api_usage
            WHERE model = ? AND request_date = ?
            """,
            (model, request_date)
        ).fetchone()

        return row[0] if row else 0
    finally:
        connection.close()


def record_ai_api_request(model: str) -> int:
    from zoneinfo import ZoneInfo

    request_date = datetime.now(
        ZoneInfo("America/Los_Angeles")
    ).date().isoformat()

    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute(
            """
            INSERT INTO ai_api_usage (
                model, request_date, request_count
            )
            VALUES (?, ?, 1)
            ON CONFLICT(model, request_date)
            DO UPDATE SET
                request_count = request_count + 1
            """,
            (model, request_date)
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT request_count
            FROM ai_api_usage
            WHERE model = ? AND request_date = ?
            """,
            (model, request_date)
        ).fetchone()

        return row[0]
    finally:
        connection.close()


def get_last_ai_request_time(model: str):
    connection = sqlite3.connect(DB_PATH)
    try:
        row = connection.execute(
            "SELECT last_request_at FROM ai_request_timing WHERE model = ?",
            (model,)
        ).fetchone()

        return datetime.fromisoformat(row[0]) if row else None
    finally:
        connection.close()


def record_ai_request_time(model: str):
    request_time = datetime.now(timezone.utc)

    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute(
            """
            INSERT INTO ai_request_timing (model, last_request_at)
            VALUES (?, ?)
            ON CONFLICT(model)
            DO UPDATE SET last_request_at = excluded.last_request_at
            """,
            (model, request_time.isoformat())
        )
        connection.commit()
    finally:
        connection.close()

    return request_time


def save_application_status(job_id: int, status: str):
    allowed_statuses = {
        "not_applied",
        "applied",
        "not_interested"
    }

    if status not in allowed_statuses:
        raise ValueError("Invalid application status")

    connection = sqlite3.connect(DB_PATH)

    connection.execute(
        """
        INSERT INTO applications (job_id, status, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(job_id) DO UPDATE SET
            status = excluded.status,
            updated_at = CURRENT_TIMESTAMP
        """,
        (job_id, status),
    )

    connection.commit()
    connection.close()


def get_application_statuses() -> dict[int, str]:
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute(
        "SELECT job_id, status FROM applications"
    ).fetchall()

    connection.close()

    return {
        job_id: status
        for job_id, status in rows
    }


def get_application_dates() -> dict[int, str]:
    connection = sqlite3.connect(DB_PATH)

    rows = connection.execute("""
        SELECT job_id, updated_at
        FROM applications
        WHERE status = 'applied'
    """).fetchall()

    connection.close()

    return {
        job_id: updated_at
        for job_id, updated_at in rows
    }


def add_to_ai_evaluation_queue(candidate_id: int, job_id: int, error: str):
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("""
            INSERT INTO ai_evaluation_queue
                (job_id, candidate_id, last_error, failed_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(job_id) DO UPDATE SET
                candidate_id = excluded.candidate_id,
                last_error = excluded.last_error,
                failed_at = CURRENT_TIMESTAMP
        """, (job_id, candidate_id, error))

        connection.commit()
    finally:
        connection.close()


def remove_from_ai_evaluation_queue(job_id: int):

    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute(
            "DELETE FROM ai_evaluation_queue WHERE job_id = ?",
            (job_id,)
        )
        connection.commit()
    finally:
        connection.close()


def get_ai_evaluation_queue_job_ids(candidate_id: int) -> set[int]:
    connection = sqlite3.connect(DB_PATH)

    try:
        rows = connection.execute("""
            SELECT job_id
            FROM ai_evaluation_queue
            WHERE candidate_id = ?
        """, (candidate_id,)).fetchall()

        return {row[0] for row in rows}
    finally:
        connection.close()


def get_ai_evaluation_queue(candidate_id: int = 1):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute("""
            SELECT
                q.job_id,
                q.candidate_id,
                q.last_error,
                q.failed_at,
                j.title,
                j.company,
                j.location,
                j.description,
                j.url,
                j.source
            FROM ai_evaluation_queue q
            JOIN jobs j ON j.id = q.job_id
            WHERE q.candidate_id = ?
            ORDER BY q.failed_at ASC
        """, (candidate_id,)).fetchall()

        return [dict(row) for row in rows]
    finally:
        connection.close()



