import httpx
from app.collectors.greenhouse_discovery import extract_greenhouse_token, save_discovered_greenhouse_board
from datetime import datetime, timedelta, timezone

url = "https://hn.algolia.com/api/v1/search_by_date"

one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

params = {
    "query": "greenhouse.io",
    "tags": "story",
    "hitsPerPage": 100,
    "numericFilters": f"created_at_i>{int(one_year_ago.timestamp())}"
}

response = httpx.get(url, params=params, timeout=20.0)
response.raise_for_status()

data = response.json()

print(f"Matching Hacker News stories: {data['nbHits']}")
print(f"Results returned: {len(data['hits'])}")

tokens = set()

for hit in data["hits"]:
    link = hit.get("url")

    if not link:
        continue

    token = extract_greenhouse_token(link)

    if token:
        tokens.add(token)

print(f"\nUnique Greenhouse company tokens: {len(tokens)}")

new_boards = 0

for token in sorted(tokens):
    board_url = f"https://boards.greenhouse.io/{token}"

    if save_discovered_greenhouse_board(board_url):
        new_boards += 1

print(f"\nNew Greenhouse boards saved: {new_boards}")