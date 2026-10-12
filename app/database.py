import sqlite3
from app.models import Job, CandidateAnalysis, CandidateProfile, JobMatchAnalysis


def initialize_database():
    connection = sqlite3.connect('data/jobhunter.db')

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
            source TEXT NOT NULL
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

    connection.close()


def get_candidate_profile():
    connection = sqlite3.connect("data/jobhunter.db")
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


def add_job(job : Job):
    connection = sqlite3.connect("data/jobhunter.db")

    try:
        connection.execute(
            """
            INSERT INTO jobs (
                title,
                company,
                location,
                description,
                url,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                job.title,
                job.company,
                job.location,
                job.description,
                job.url,
                job.source
            )
        )

        connection.commit()
        return True
    
    except sqlite3.IntegrityError:
        return False
    
    finally:
        connection.close()


def get_jobs():
    connection = sqlite3.connect("data/jobhunter.db")
    connection.row_factory = sqlite3.Row

    results = connection.execute(
        """
        SELECT id, title, company, location, description, url, source
        FROM jobs
        """
    ).fetchall()

    connection.close()

    return results


def get_candidate_analysis(candidate_id: int) -> CandidateAnalysis | None:
    connection = sqlite3.connect("data/jobhunter.db")
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

        return CandidateAnalysis.model_validate_json(
            row["analysis_json"]
        )

    finally:
        connection.close()


def save_candidate_analysis(candidate_id: int, analysis: CandidateAnalysis):
    connection = sqlite3.connect("data/jobhunter.db")

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

    connection = sqlite3.connect("data/jobhunter.db")

    try:
        connection.execute("""
            INSERT INTO job_match_analysis (
                candidate_id,
                job_id,
                analysis_json
            )
            VALUES (?, ?, ?)
            ON CONFLICT(candidate_id, job_id)
            DO UPDATE SET
                analysis_json = excluded.analysis_json
        """, (
            candidate_id,
            job_id,
            analysis.model_dump_json()
        ))

        connection.commit()

    finally:
        connection.close()


def get_job_match_analysis(candidate_id: int, job_id: int) -> JobMatchAnalysis | None:

    connection = sqlite3.connect("data/jobhunter.db")
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.execute("""
            SELECT analysis_json
            FROM job_match_analysis
            WHERE candidate_id = ?
              AND job_id = ?
        """, (candidate_id, job_id))

        row = cursor.fetchone()

        if row is None:
            return None

        return JobMatchAnalysis.model_validate_json(
            row["analysis_json"]
        )

    finally:
        connection.close()