from app.ai_service import analyse_job_match
from app.config import EXCLUDED_JOB_KEYWORDS, PREFERRED_JOB_KEYWORDS
from app.database import get_jobs, get_candidate_profile, get_candidate_analysis, get_job_match_analysis, save_job_match_analysis
from app.matching import get_matching_jobs
from app.models import Job



def get_jobs_for_ai_analysis(limit: int = 5):
    candidate = get_candidate_profile()
    jobs = get_jobs()

    matches = get_matching_jobs(jobs, candidate)

    real_matches = [
        match for match in matches
        if match["job"]["company"] != "Test Company"
        and not EXCLUDED_JOB_KEYWORDS.intersection(
            match["job"]["title"]
            .lower()
            .replace("-", " ")
            .replace("/", " ")
            .split()
        )
    ]

    ranked_matches = sorted(
        real_matches,
        key=lambda match: (
            any(
                keyword in match["job"]["title"].lower()
                for keyword in PREFERRED_JOB_KEYWORDS
            ),
            match["score"]
        ),
        reverse=True
    )

    return ranked_matches[:limit]


def evaluate_jobs_with_ai(candidate_id: int = 1, limit: int = 5, max_evaluations: int = 10, max_api_calls: int = 2):
    candidate = get_candidate_analysis(candidate_id)

    if candidate is None:
        raise ValueError("No saved candidate analysis found.")

    matches = get_jobs_for_ai_analysis(max_evaluations)
    results = []
    api_calls = 0

    for match in matches:
        job_row = match["job"]
        job_id = job_row["id"]

        analysis = get_job_match_analysis(candidate_id, job_id)

        if analysis is None:
            if api_calls >= max_api_calls:
                print(f"Skipping uncached job (API limit reached): {job_row['title']}")
                continue

            api_calls += 1

            print(f"Calling Gemini: {job_row['title']} at {job_row['company']}")

            job = Job(
                title=job_row["title"],
                company=job_row["company"],
                location=job_row["location"],
                description=job_row["description"],
                url=job_row["url"],
                source=job_row["source"]
            )

            analysis = analyse_job_match(candidate, job)

            save_job_match_analysis(candidate_id, job_id, analysis)

        else:
            print(f"Using cached analysis: {job_row['title']}")

        if analysis.eligibility == "ineligible":
            continue

        results.append({
            "job": job_row,
            "analysis": analysis
        })

        if len(results) >= limit:
            break

    eligible_results = [
        result for result in results
        if result["analysis"].eligibility != "ineligible"
    ]

    return sorted(
        results,
        key=lambda result: (
            result["analysis"].eligibility == "eligible",
            result["analysis"].score
        ),
        reverse=True
    )