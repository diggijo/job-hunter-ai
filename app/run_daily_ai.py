from app.ai_job_evaluation import run_locked_ai_evaluation
from app.config import DAILY_AI_LIMIT, MIN_MATCH_SCORE
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true"
    )
    args = parser.parse_args()

    max_requests = 0 if args.dry_run else DAILY_AI_LIMIT

    print(
        "Starting daily AI job evaluation..."
        + (" (DRY RUN)" if args.dry_run else "")
    )

    results = run_locked_ai_evaluation(
        candidate_id=1,
        limit=25,
        max_evaluations=max_requests,
        max_api_calls=max_requests
    )

    eligible_results = [
        result for result in results
        if result["analysis"].eligibility == "eligible"
    ]

    unknown_results = [
        result for result in results
        if result["analysis"].eligibility == "unknown"
    ]

    print(f"\nEligible matches: {len(eligible_results)}")
    print(f"Unknown eligibility: {len(unknown_results)}")

    
    recommended_results = eligible_results + unknown_results

    recommended_results.sort(
        key=lambda result: result["analysis"].score,
        reverse=True,
    )

    print("\nRecommended jobs:")

    for result in recommended_results:
        job = result["job"]
        analysis = result["analysis"]

        if analysis.score < MIN_MATCH_SCORE:
            continue

        status = (
            "Eligible"
            if analysis.eligibility == "eligible"
            else "Eligibility needs verification"
        )

        print(
            f"{analysis.score}/100 | "
            f"{job['company']} | "
            f"{job['title']} | "
            f"{job['location']} | "
            f"{status}"
        )


if __name__ == "__main__":
    main()
