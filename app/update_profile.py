import sqlite3


connection = sqlite3.connect("data/jobhunter.db")

candidate = connection.execute(
    "SELECT id FROM candidate_profile LIMIT 1"
).fetchone()

candidate_id = candidate[0]

connection.execute(
    "DELETE FROM preferred_roles WHERE candidate_id = ?",
    (candidate_id,)
)

roles = [
    "software",
    "game",
    "machine",
    "unity",
    "graduate"
]

for role in roles:
    connection.execute(
        """
        INSERT INTO preferred_roles (candidate_id, role)
        VALUES (?, ?)
        """,
        (candidate_id, role)
    )

connection.commit()
connection.close()

print("Preferred roles updated.")