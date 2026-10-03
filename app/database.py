import sqlite3
from app.models import Job


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