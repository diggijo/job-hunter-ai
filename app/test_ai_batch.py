from app.ai_matching import run_locked_ai_evaluation


results = run_locked_ai_evaluation(
    candidate_id=1,
    limit=10,
    max_evaluations=0,
    max_api_calls=0
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