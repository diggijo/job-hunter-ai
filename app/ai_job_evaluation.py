from app.ai_service import analyse_job_match
from app.config import EXCLUDED_JOB_KEYWORDS, EXPERIENCE_NUMBER_WORDS, MAX_REQUIRED_EXPERIENCE, GEMINI_MODEL, GEMINI_REQUEST_DELAY
from app.database import *
from app.job_filters import get_job_priority
from app.job_matching import get_matching_jobs, location_matches
from app.models import Job
from collections import defaultdict
from datetime import datetime, timezone
from filelock import FileLock, Timeout
from google.genai import errors
import re
import time


def meets_experience_requirement(description: str) -> bool:
    number_pattern = r"\d+|" + "|".join(EXPERIENCE_NUMBER_WORDS.keys())

    pattern = (
        rf"\b({number_pattern})\b"
        rf"(?:\s*[-â€“â€”]\s*({number_pattern}))?"
        rf"(\+)?\s*(?:years?|yrs?)\b"
        rf"(?:(?:\W+\w+){{0,6}}?\W+experience\b"
        rf"|\s+(?:in|of)\s+\w+)?"
    )

    for match in re.finditer(pattern, description.lower()):
        # Use the upper number if an experience range is provided
        value = match.group(2) or match.group(1)

        # Check whether the experience is preferred rather than required
        following_text = description[match.end():match.end() + 40].lower()

        if re.match(
            r"\s*(?:is\s+)?(?:preferred|bonus|desirable|a plus)\b",
            following_text
        ):
            continue

        years = (
            int(value)
            if value.isdigit()
            else EXPERIENCE_NUMBER_WORDS[value]
        )

        has_plus = match.group(3) is not None

        if years >= MAX_REQUIRED_EXPERIENCE and match.group(2) is None:
            return False

        if years > MAX_REQUIRED_EXPERIENCE:
            return False

    return True


def job_priority(match):
    return get_job_priority(match["job"]["title"])


def diversify_jobs(ranked_matches):
    grouped = defaultdict(list)

    for match in ranked_matches:
        grouped[job_priority(match)].append(match)

    diversified = []

    for priority in sorted(grouped):
        company_groups = defaultdict(list)

        for match in grouped[priority]:
            company = match["job"]["company"]
            company_groups[company].append(match)

        while any(company_groups.values()):
            for jobs in company_groups.values():
                if jobs:
                    diversified.append(jobs.pop(0))

    return diversified


def get_jobs_for_ai_analysis(limit: int = 5, candidate_id: int = 1):
    candidate = get_candidate_profile()
    jobs = get_jobs()

    matches = get_matching_jobs(jobs, candidate)

    application_statuses = get_application_statuses()

    matches = [
        match for match in matches
        if application_statuses.get(match["job"]["id"]) != "not_interested"
    ]

    real_matches = [
        match for match in matches
        if match["job"]["company"] != "Test Company"
        and location_matches(match["job"]["location"], candidate["preferred_locations"])
        and meets_experience_requirement(match["job"]["description"])
        and not EXCLUDED_JOB_KEYWORDS.intersection(
            re.findall(r"[a-z]+", match["job"]["title"].lower())
        )
    ]

    ranked_matches = sorted(
        real_matches,
        key=job_priority
    )

    ranked_matches = diversify_jobs(ranked_matches)

    queued_job_ids = get_ai_evaluation_queue_job_ids(candidate_id)
    eligible_candidates = []

    for match in ranked_matches:
        job_id = match["job"]["id"]

        if job_id in queued_job_ids:
            continue

        cached_analysis = get_job_match_analysis(candidate_id, job_id)

        if cached_analysis is not None and cached_analysis.eligibility == "ineligible":
            continue

        eligible_candidates.append(match)

        if len(eligible_candidates) >= limit:
            break

    return eligible_candidates


def evaluate_jobs_with_ai(candidate_id: int = 1, limit: int = 5, max_evaluations: int = 10, max_api_calls: int = 2):
    candidate = get_candidate_analysis(candidate_id)

    if candidate is None:
        raise ValueError("No saved candidate analysis found.")

    matches = get_jobs_for_ai_analysis(limit=len(get_jobs()), candidate_id=candidate_id)

    matches.sort(
        key=lambda match: (
            get_job_match_analysis(candidate_id, match["job"]["id"]) is not None,
            get_job_priority(match["job"]["title"])
        )
    )

    def queue_remaining_jobs(error_message: str):
        queued = 0
        existing_queued_ids = get_ai_evaluation_queue_job_ids(candidate_id)

        for remaining_match in matches:
            remaining_job_id = remaining_match["job"]["id"]
            if remaining_job_id in existing_queued_ids:
                continue

            if get_job_match_analysis(candidate_id, remaining_job_id) is not None:
                continue

            add_to_ai_evaluation_queue(
                candidate_id,
                remaining_job_id,
                error_message
            )
            queued += 1

        print(f"Jobs awaiting evaluation in queue: {queued}")

    results = []
    api_calls = 0

    for match in matches:
        job_row = match["job"]
        job_id = job_row["id"]

        analysis = get_job_match_analysis(candidate_id, job_id)

        if analysis is None:
            if api_calls >= max_api_calls or api_calls >= max_evaluations:
                if max_api_calls > 0 and max_evaluations > 0:
                    queue_remaining_jobs(
                        "Pending evaluation: Gemini batch request limit reached"
                    )

                print("Gemini batch request limit reached.")
                break

            daily_usage = get_daily_ai_usage(GEMINI_MODEL)

            print(
                f"Calling Gemini (attempt {daily_usage + 1} today): "
                f"{job_row['title']} at {job_row['company']}"
            )

            job = Job(
                title=job_row["title"],
                company=job_row["company"],
                location=job_row["location"],
                description=job_row["description"],
                url=job_row["url"],
                source=job_row["source"]
            )

            analysis = None

            try:
                if api_calls >= max_api_calls:
                    print("Gemini batch request limit reached.")
                    break

                last_request_time = get_last_ai_request_time(GEMINI_MODEL)

                if last_request_time is not None:
                    elapsed = (
                        datetime.now(timezone.utc) - last_request_time
                    ).total_seconds()

                    remaining_delay = GEMINI_REQUEST_DELAY - elapsed

                    if remaining_delay > 0:
                        time.sleep(remaining_delay)

                record_ai_request_time(GEMINI_MODEL)

                api_calls += 1
                daily_usage = record_ai_api_request(GEMINI_MODEL)

                print(
                    f"Gemini request #{daily_usage} today: "
                    f"{job_row['title']}"
                )

                analysis = analyse_job_match(candidate, job)
                save_job_match_analysis(candidate_id, job_id, analysis)
                remove_from_ai_evaluation_queue(job_id)

            except errors.APIError as error:
                print(f"Gemini API error ({error.code}): {job_row['title']}")

                add_to_ai_evaluation_queue(
                    candidate_id,
                    job_id,
                    f"Gemini API error {error.code}: {error}"
                )

                if error.code == 429:
                    print("Gemini quota or rate limit reached.")

                    queue_remaining_jobs(
                        "Pending evaluation: Gemini quota or rate limit reached (429)"
                    )

                    print("Remaining jobs added to the retry queue.")
                    break

            except Exception as error:
                print(f"Gemini evaluation failed: {job_row['title']}")
                print(f"Error: {error}")

                add_to_ai_evaluation_queue(
                    candidate_id,
                    job_id,
                    str(error)
                )

            if analysis is None:
                if api_calls >= max_api_calls or api_calls >= max_evaluations:
                    queue_remaining_jobs(
                        "Pending evaluation: Gemini batch request limit reached"
                    )
                    print("Gemini batch request limit reached. Stopping.")
                    break

                print(
                    f"Gemini evaluation failed. Skipping: "
                    f"{job_row['title']}"
                )
                continue

        else:
            print(f"Using cached analysis: {job_row['title']}")

        results.append({"job": job_row, "analysis": analysis})

    return sorted(
        results,
        key=lambda result: (
            result["analysis"].eligibility == "eligible",
            result["analysis"].score
        ),
        reverse=True
    )[:limit]


def run_locked_ai_evaluation(candidate_id: int = 1, limit: int = 10, max_evaluations: int = 10, max_api_calls: int = 10):
    lock = FileLock("data/ai_evaluation.lock", timeout=0)

    try:
        with lock:
            return evaluate_jobs_with_ai(
                candidate_id=candidate_id,
                limit=limit,
                max_evaluations=max_evaluations,
                max_api_calls=max_api_calls
            )
    except Timeout:
        print("Another AI evaluation batch is already running.")
        return []