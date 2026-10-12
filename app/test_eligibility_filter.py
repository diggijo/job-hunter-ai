from app.models import JobMatchAnalysis


def make_result(title, score, eligibility):
    return {
        "job": {"title": title},
        "analysis": JobMatchAnalysis(
            score=score,
            eligibility=eligibility,
            eligibility_reasons=[],
            strengths=[],
            gaps=[],
            explanation="Test evaluation"
        )
    }


results = [
    make_result("Software Engineer", 80, "eligible"),
    make_result("Software Developer Intern", 95, "ineligible"),
    make_result("Backend Developer", 90, "unknown"),
    make_result("Junior Software Engineer", 75, "eligible"),
]

eligible_results = [
    result for result in results
    if result["analysis"].eligibility != "ineligible"
]

ranked_results = sorted(
    eligible_results,
    key=lambda result: (
        result["analysis"].eligibility == "eligible",
        result["analysis"].score
    ),
    reverse=True
)

for result in ranked_results:
    print(
        f"{result['job']['title']} | "
        f"{result['analysis'].score}/100 | "
        f"{result['analysis'].eligibility}"
    )