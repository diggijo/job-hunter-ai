from app.ai_matching import evaluate_jobs_with_ai


results = evaluate_jobs_with_ai(
    candidate_id=1,
    limit=10,
    max_evaluations=3,
    max_api_calls=3
)

print("\nAI Job Matching Results\n")

for result in results:
    job = result["job"]
    analysis = result["analysis"]

    print(f"Job: {job['title']}")
    print(f"Company: {job['company']}")
    print(f"AI Score: {analysis.score}/100")
    print(f"Eligibility: {analysis.eligibility}")

    print("\nEligibility Reasons:")
    for reason in analysis.eligibility_reasons:
        print(f"  - {reason}")

    print("\nStrengths:")
    for strength in analysis.strengths:
        print(f"  + {strength}")

    print("\nGaps:")
    for gap in analysis.gaps:
        print(f"  - {gap}")

    print(f"\nExplanation: {analysis.explanation}")