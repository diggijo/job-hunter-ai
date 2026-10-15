import csv
import io
import httpx
from app.database import add_greenhouse_board, get_greenhouse_boards


url = (
    "https://raw.githubusercontent.com/"
    "kalebconfer-sys/job-board-directory/"
    "main/greenhouse.csv"
)

response = httpx.get(url, timeout=30.0)
response.raise_for_status()

reader = csv.DictReader(io.StringIO(response.text))

print("CSV columns:", reader.fieldnames)

rows = list(reader)

print("Greenhouse boards in dataset:", len(rows))

added_count = 0

for row in rows:
    if row["platform"] != "greenhouse":
        continue

    token = row["token"].strip()
    company = row["company"].strip()

    if not token:
        continue

    if add_greenhouse_board(token, company):
        added_count += 1

print(f"\nNew boards imported: {added_count}")
print(f"Total boards in SQLite: {len(get_greenhouse_boards())}")