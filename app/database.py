import sqlite3


connection = sqlite3.connect('data/jobhunter.db')

connection.execute("""
    CREATE TABLE IF NOT EXISTS candidate_profile (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )
""")

connection.close()

def get_candidate_profile():
    connection = sqlite3.connect('data/jobhunter.db')
    connection.row_factory = sqlite3.Row

    result = connection.execute(
        "SELECT id, name FROM candidate_profile LIMIT 1"
    ).fetchone()

    connection.close()

    return result