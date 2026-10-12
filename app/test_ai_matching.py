from app.ai_matching import get_jobs_for_ai_analysis


matches = get_jobs_for_ai_analysis(limit=5)

print(f"Selected {len(matches)} jobs for AI analysis.\n")

for index, match in enumerate(matches, start=1):
    job = match["job"]

    print(f"{index}. {job['title']}")
    print(f"   Company: {job['company']}")
    print(f"   Location: {job['location']}")
    print(f"   Keyword score: {match['score']}")
    print(f"   Job ID: {job['id']}")
    print()