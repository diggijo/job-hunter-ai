from app.ai_matching import evaluate_jobs_with_ai

results = evaluate_jobs_with_ai(
    candidate_id=1,
    limit=10,
    max_evaluations=0,
    max_api_calls=0
)

print(f"\nResults returned: {len(results)}")

for result in results:
    job = result["job"]
    analysis = result["analysis"]

    print(
        f"{job['company']} | {job['title']} | "
        f"{analysis.eligibility} | {analysis.score}/100"
    )
