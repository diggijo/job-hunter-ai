import sqlite3


connection = sqlite3.connect("data/jobhunter.db")

connection.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_url
    ON jobs (url)
""")

connection.commit()
connection.close()

print("Database migration completed.")