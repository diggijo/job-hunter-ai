import sqlite3


connection = sqlite3.connect("data/jobhunter.db")

candidate_id = 1

preferred_roles = [
    "Software Engineer",
    "Gameplay Programmer",
    "Machine Learning Engineer",
    "Unity Developer"
]

preferred_locations = [
    "Ireland",
    "London",
    "New York",
    "Remote"
]

for role in preferred_roles:
    connection.execute(
        "INSERT INTO preferred_roles (candidate_id, role) VALUES (?, ?)",
        (candidate_id, role)
    )

for location in preferred_locations:
    connection.execute(
        "INSERT INTO preferred_locations (candidate_id, location) VALUES (?, ?)",
        (candidate_id, location)
    )

connection.commit()
connection.close()