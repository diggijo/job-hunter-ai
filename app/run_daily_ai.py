from app.ai_job_evaluation import run_locked_ai_evaluation
from app.config import DAILY_AI_LIMIT
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

    for result in eligible_results:
        job = result["job"]
        analysis = result["analysis"]

        print(
            f"{analysis.score}/100 | "
            f"{job['company']} | "
            f"{job['title']} | "
            f"{analysis.eligibility}"
        )


if __name__ == "__main__":
    main()
